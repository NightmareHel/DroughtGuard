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
    """Get list of regions from dataset."""
    regions = features_df['region'].tolist()
    return jsonify({'regions': regions})

@app.route('/api/predict', methods=['POST'])
def predict():
    """Predict food insecurity risk for a region."""
    data = request.get_json()
    region = data.get('region')
    
    if not region:
        return jsonify({'error': 'Region is required'}), 400

    # ✅ Normalize region name if needed
    mapped_name = REGION_MAP.get(region, region)
    
    # Get features for region
    region_data = features_df[features_df['region'] == region]
    if region_data.empty:
        return jsonify({'error': 'Region not found'}), 404
    
    features = region_data[['month', 'ndvi_anomaly', 'rainfall_anomaly', 'food_price_inflation', 'temp_anomaly']].iloc[0]
    print("🧾 Features for prediction:", features.to_dict())


    # Make prediction
    probability = predict_risk(features.to_dict())
    risk_category = categorize_risk(probability)
    
    # ✅ Return mapped_name (so it matches GeoJSON)
    return jsonify({
        'region': mapped_name,
        'probability': float(probability),
        'risk_category': risk_category,
        'features': features.to_dict()
    })

@app.route('/api/map-data')
def get_map_data():
    """Get GeoJSON data for map visualization."""
    return jsonify(geojson_data)

if __name__ == '__main__':
    print("✅ Starting DroughtGuard Flask app...")
    app.run(debug=True, host='0.0.0.0', port=5000)
