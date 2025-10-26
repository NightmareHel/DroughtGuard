"""
Main Flask application for DroughtGuard.
"""
from flask import Flask, render_template, jsonify, request
import pandas as pd
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from predict import predict_risk
from utils.data_loader import load_geojson, load_features
from utils.categorizer import categorize_risk

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
    regions = features_df['region'].unique().tolist()
    return jsonify({'regions': regions})

@app.route('/api/predict', methods=['POST'])
def predict():
    """Predict food insecurity risk for a region across multiple time horizons."""
    data = request.get_json()
    region = data.get('region')
    
    if not region:
        return jsonify({'error': 'Region is required'}), 400
        
    try:
        # Get latest features for the region
        region_features = features_df[features_df['region'] == region].iloc[-1].to_dict()
        
        # Get predictions for all horizons
        probabilities = predict_risk(region_features)
        
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
        return jsonify({
            'error': f'Prediction failed: {str(e)}'
        }), 500

@app.route('/api/map-data')
def get_map_data():
    """Get GeoJSON data for map visualization."""
    return jsonify(geojson_data)

if __name__ == '__main__':
    print("[OK] Starting DroughtGuard Flask app...")
    app.run(debug=True, host='0.0.0.0', port=5000)
