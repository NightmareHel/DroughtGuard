"""
Data loading utilities.
"""
import pandas as pd
import json
import os

def load_geojson():
    """Load Kenya regions GeoJSON file."""
    geojson_path = os.path.join('app', 'static', 'geo', 'kenya.json')
    
    if os.path.exists(geojson_path):
        with open(geojson_path, 'r') as f:
            return json.load(f)
    
    return {}

def load_features():
    """Load regional features CSV."""
    features_path = os.path.join('data', 'features.csv')
    
    if os.path.exists(features_path):
        return pd.read_csv(features_path)
    
    # Return empty DataFrame if file doesn't exist
    return pd.DataFrame()
