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

print("[DEBUG] GEMINI_API_KEY starts with:", os.getenv("GEMINI_API_KEY", "")[:6])
print("[DEBUG] GEMINI_MODEL:", os.getenv("GEMINI_MODEL"))
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
    data = request.get_json()
    region = data.get('region')

    region_data = features_df[features_df['region'] == region]
    if region_data.empty:
        return jsonify({'error': f'Region not found: {region}'}), 404

    # get the latest entry for that region
    features = region_data.iloc[-1].to_dict()
    print(f"🧾 Features used for prediction ({region}):", {k:v for k,v in features.items() if 'lag' in k})


    print(f"🧾 Features for prediction: {features}")

    try:
        # Get probabilities for all horizons
        probabilities = predict_risk(features)
        print(f"🔮 Raw probabilities: {probabilities}")

        # Build structured prediction objects expected by the frontend
        predictions = {}
        for h, prob in probabilities.items():
            cat = categorize_risk(prob)
            predictions[h] = {
                "probability": prob,
                "category": cat["label"],
                "color": cat["color"]
            }

        # Return consistent format
        return jsonify({
            "region": region,
            "display_name": region,
            "predictions": predictions
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error predicting risk: {str(e)}'}), 500


@app.route('/api/map-data')
def get_map_data():
    """Get GeoJSON data for map visualization."""
    return jsonify(geojson_data)

if __name__ == '__main__':
    print("[OK] Starting DroughtGuard Flask app...")
    print(f"[OK] Gemini model: {os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')}")
    app.run(debug=True, host='0.0.0.0', port=5000)
