"""
Main Flask application for DroughtGuard.
"""
from __future__ import annotations

import os
import sys
import traceback
from datetime import datetime

from flask import Flask, render_template, jsonify, request
import pandas as pd

# -------------------------------------------------------------------
# 0) Load .env EARLY so AI modules see keys at import time
# -------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[OK] .env loaded early")
except Exception as _e:
    print(f"[WARN] dotenv not available or failed: {_e}")

# Ensure local utils are importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# -------------------------------------------------------------------
# 1) Core app imports
# -------------------------------------------------------------------
from predict import predict_risk
from utils.data_loader import load_geojson, load_features
from utils.categorizer import categorize_risk

# -------------------------------------------------------------------
# 2) AI Advisor import with diagnostics (llm_chain + ai_cache)
#    NOTE: If your llm_chain tries to configure Gemini at import-time,
#    it must tolerate missing GEMINI_API_KEY or defer config until use.
# -------------------------------------------------------------------
AI_ADVISOR_AVAILABLE = False

try:
    from utils.llm_chain import get_explanation, get_brief, setup_cache, gemini_ready
    from utils.ai_cache import ai_cache
    try:
        # initialize any caches / clients the module wants
        setup_cache()
    except Exception as _e:
        print(f"[WARN] setup_cache() failed: {_e}")
    AI_ADVISOR_AVAILABLE = True
    print("[OK] AI Advisor module loaded")
except Exception as e:
    print("[WARNING] AI Advisor not available.")
    traceback.print_exc()
    # Safe stubs so routes can respond with 503
    def get_explanation(*args, **kwargs): raise NotImplementedError("AI Advisor not available")
    def get_brief(*args, **kwargs): raise NotImplementedError("AI Advisor not available")
    def setup_cache(): pass
    # simple no-op cache
    ai_cache = type('obj', (object,), {'get': lambda *a, **k: None, 'set': lambda *a, **k: None})()
    # health helper when module missing
    def gemini_ready():
        # Tell caller exactly what's missing
        try:
            import google.generativeai  # noqa
            has_pkg = True
        except Exception:
            has_pkg = False
        key = bool(os.getenv("GEMINI_API_KEY"))
        if not has_pkg:
            return (False, "google-generativeai package not installed")
        if not key:
            return (False, "GEMINI_API_KEY missing")
        return (False, "llm_chain import failed (see server logs)")

# -------------------------------------------------------------------
# 3) Flask app
# -------------------------------------------------------------------
app = Flask(__name__)

# Load data once at startup
geojson_data = load_geojson()
features_df = load_features()

# ✅ Region mapping: your dataset cities → GeoJSON counties
REGION_MAP = {
    "Eldoret": "Uasin Gishu",
    "Thika": "Kiambu",
    "Malindi": "Kilifi",
    "Kitale": "Trans Nzoia",
    # others match themselves (no mapping needed)
}

@app.route('/')
def index():
    """Render main dashboard."""
    return render_template('index.html')

@app.route('/api/regions')
def get_regions():
    """Get list of unique regions from dataset."""
    regions = features_df['region'].dropna().astype(str).unique().tolist()
    return jsonify({'regions': regions})

@app.route('/api/map-data')
def get_map_data():
    """Get GeoJSON data for map visualization."""
    return jsonify(geojson_data)

# -------------------------------------------------------------------
# 4) Prediction endpoint (unchanged)
# -------------------------------------------------------------------
@app.route('/api/predict', methods=['POST'])
def predict():
    """Predict food insecurity risk for a region across multiple time horizons."""
    data = request.get_json(silent=True) or {}
    region = data.get('region')

    if not region:
        return jsonify({'error': 'Region is required'}), 400

    try:
        # Get latest features for the region
        region_rows = features_df[features_df['region'] == region]
        if region_rows.empty:
            return jsonify({'error': f'Region not found in dataset: {region}'}), 404

        latest = region_rows.iloc[-1].to_dict()

        # Get predictions for all horizons
        probabilities = predict_risk(latest)

        # Categorize risk for each horizon
        predictions = {}
        for horizon, prob in probabilities.items():
            risk_category = categorize_risk(prob, horizon)
            predictions[horizon] = {
                'probability': prob,
                'category': risk_category['label'],
                'color': risk_category['color']
            }

        # Map region name if needed
        display_name = REGION_MAP.get(region, region)

        return jsonify({
            'region': region,
            'display_name': display_name,
            'predictions': predictions
        })
    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

# -------------------------------------------------------------------
# 5) Helpers for AI facts & month
# -------------------------------------------------------------------
def collect_region_facts(region: str, horizon: int) -> dict:
    """
    Collect facts for a region and horizon.
    Returns a dict with probability and signal facts for prompting.
    """
    region_rows = features_df[features_df['region'] == region]
    if region_rows.empty:
        raise ValueError(f"Region not found: {region}")

    latest = region_rows.iloc[-1]

    # Predict for this horizon
    probabilities = predict_risk(latest.to_dict())
    prob = float(probabilities.get(horizon, 0.0))

    # Categorize risk
    risk_category = categorize_risk(prob, horizon)

    # Collect facts (use your column names)
    facts = {
        "prob": prob,
        "risk_tier": risk_category['label'],
        "ndvi_anomaly": latest.get('ndvi_anomaly', None),
        "spi1": None,   # Not present in current dataset
        "spi3": None,   # Not present in current dataset
        "price_yoy": latest.get('food_price_inflation', None),
    }

    # Deltas if available
    try:
        if latest.get('ndvi_anomaly_lag1') is not None and latest.get('ndvi_anomaly') is not None:
            facts["delta_ndvi"] = float(latest['ndvi_anomaly']) - float(latest['ndvi_anomaly_lag1'])
    except Exception:
        facts["delta_ndvi"] = None

    try:
        if latest.get('food_price_inflation_lag1') is not None and latest.get('food_price_inflation') is not None:
            facts["delta_price"] = float(latest['food_price_inflation']) - float(latest['food_price_inflation_lag1'])
    except Exception:
        facts["delta_price"] = None

    app.logger.info(
        f"FACTS region={region} h={horizon}: prob={facts['prob']:.3f} "
        f"ndvi={facts.get('ndvi_anomaly')} price_yoy={facts.get('price_yoy')}"
    )
    return facts


def get_current_month() -> str:
    """Get current month string (YYYY-MM) from latest data."""
    if not features_df.empty and 'month' in features_df.columns:
        max_month = str(features_df['month'].iloc[-1])
        return max_month.replace('/', '-')  # e.g., "2024/12" -> "2024-12"
    return datetime.now().strftime('%Y-%m')

# -------------------------------------------------------------------
# 6) AI Health
# -------------------------------------------------------------------
@app.route('/api/ai/health')
def ai_health():
    ok, reason = gemini_ready()
    return jsonify({"gemini_ready": bool(ok), "reason": reason, "advisor_loaded": AI_ADVISOR_AVAILABLE}), (200 if ok else 503)

# -------------------------------------------------------------------
# 7) AI Advisor routes
# -------------------------------------------------------------------
@app.route('/api/explain/<region>')
def explain_region(region):
    """Get AI explanation for a region's forecast."""
    ok, reason = gemini_ready()
    if not ok:
        return jsonify({'error': 'AI Advisor not available', 'detail': reason}), 503

    try:
        horizon = int(request.args.get('h', '1'))
        force = request.args.get('force', 'false').lower() == 'true'
        if horizon not in (1, 2, 3):
            return jsonify({'error': 'Invalid horizon. Use h=1, 2, or 3'}), 400

        month_str = get_current_month()
        cache_key = (region, month_str, horizon, 'explain')

        if not force:
            cached = ai_cache.get(cache_key)
            if cached:
                return jsonify({
                    'region': region,
                    'horizon': horizon,
                    'month': month_str,
                    'cached': True,
                    'data': cached
                })

        facts = collect_region_facts(region, horizon)
        result = get_explanation(facts, region, horizon, month_str)

        ai_cache.set(cache_key, result, ttl_seconds=86400)
        return jsonify({
            'region': region,
            'horizon': horizon,
            'month': month_str,
            'cached': False,
            'data': result
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'AI explanation failed', 'detail': str(e)}), 502


@app.route('/api/brief/<region>')
def brief_region(region):
    """Get AI brief for a region's forecast."""
    ok, reason = gemini_ready()
    if not ok:
        return jsonify({'error': 'AI Advisor not available', 'detail': reason}), 503

    try:
        horizon = int(request.args.get('h', '1'))
        force = request.args.get('force', 'false').lower() == 'true'
        if horizon not in (1, 2, 3):
            return jsonify({'error': 'Invalid horizon. Use h=1, 2, or 3'}), 400

        month_str = get_current_month()
        cache_key = (region, month_str, horizon, 'brief')

        if not force:
            cached = ai_cache.get(cache_key)
            if cached:
                return jsonify({
                    'region': region,
                    'horizon': horizon,
                    'month': month_str,
                    'cached': True,
                    'data': cached
                })

        facts = collect_region_facts(region, horizon)
        result = get_brief(facts, region, horizon, month_str)

        ai_cache.set(cache_key, result, ttl_seconds=86400)
        return jsonify({
            'region': region,
            'horizon': horizon,
            'month': month_str,
            'cached': False,
            'data': result
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'AI brief failed', 'detail': str(e)}), 502


if __name__ == '__main__':
    print("[OK] Starting DroughtGuard Flask app...")
    print(f"[OK] Gemini model: {os.getenv('GEMINI_MODEL', 'gemini-1.5-pro-latest')}")
    app.run(debug=True, host='0.0.0.0', port=5000)
