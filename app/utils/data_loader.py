"""
Data loading utilities.
"""
import pandas as pd
import json
import os

# Move one level up from /app/utils → project root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def load_geojson():
    """Load Kenya regions GeoJSON file and normalize property names."""
    geojson_path = os.path.join(BASE_DIR, 'app', 'static', 'geo', 'kenya.json')
    try:
        with open(geojson_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"[OK] Loaded GeoJSON: {geojson_path}")
    except Exception as e:
        print(f"[ERROR] Failed to read GeoJSON: {e}")
        return {}

    # Normalize property names so JS can read feature.properties.name
    for feat in data.get("features", []):
        props = feat.get("properties", {})
        name = (
            props.get("shapeName")
            or props.get("ADM1_NAME")
            or props.get("COUNTY")
            or props.get("NAME_1")
        )
        if name:
            props["name"] = name.strip().title()
    return data

def load_features():
    """Load regional features CSV."""
    features_path = os.path.join(BASE_DIR, 'data', 'features.csv')

    if os.path.exists(features_path):
        df = pd.read_csv(features_path)
        # Normalize column names to lowercase
        df.columns = [c.strip().lower() for c in df.columns]
        print(f"[OK] Loaded features from: {features_path}")
        print("Columns:", df.columns.tolist())
        return df
    
    print(f"[ERROR] Features CSV not found at: {features_path}")
    return pd.DataFrame()
