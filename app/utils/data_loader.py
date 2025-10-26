"""
Utility functions for loading and validating DroughtGuard datasets and GeoJSON.
This version assumes data/features.csv does NOT contain a 'month' column.
"""

import os
import json
import pandas as pd

# --------------------------------------------------------------------
# PATH CONFIGURATION
# --------------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir, os.pardir))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
GEO_DIR = os.path.join(PROJECT_ROOT, "app", "static", "geo")

FEATURES_PATH = os.path.join(DATA_DIR, "features.csv")
GEOJSON_PATH = os.path.join(GEO_DIR, "kenya.json")

# --------------------------------------------------------------------
# DATA LOADING
# --------------------------------------------------------------------
def load_features() -> pd.DataFrame:
    """Load and validate the feature dataset."""
    if not os.path.exists(FEATURES_PATH):
        raise FileNotFoundError(f"❌ features.csv not found at {FEATURES_PATH}")

    df = pd.read_csv(FEATURES_PATH)
    print(f"✅ Loaded features from {FEATURES_PATH}")
    print(f"📄 Columns found: {df.columns.tolist()}")

    # Minimal expected columns (no 'month')
    required = [
        "region",
        "ndvi_anomaly",
        "rainfall_anomaly",
        "food_price_inflation",
        "temp_anomaly",
        "risk_label",
        "ndvi_anomaly_lag1",
        "ndvi_anomaly_lag2",
        "rainfall_anomaly_lag1",
        "rainfall_anomaly_lag2",
        "food_price_inflation_lag1",
        "food_price_inflation_lag2",
        "temp_anomaly_lag1",
        "temp_anomaly_lag2",
    ]

    missing = [col for col in required if col not in df.columns]
    if missing:
        print(f"⚠️ Warning: Missing columns in features.csv: {missing}")
    else:
        print("✅ All expected feature columns present.")

    # Basic cleaning
    df = df.fillna(0)
    df["region"] = df["region"].astype(str)

    return df

# --------------------------------------------------------------------
# GEOJSON LOADING
# --------------------------------------------------------------------
def load_geojson() -> dict:
    """Load the Kenya GeoJSON file used for mapping regions."""
    if not os.path.exists(GEOJSON_PATH):
        raise FileNotFoundError(f"❌ GeoJSON file not found at {GEOJSON_PATH}")

    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    print(f"✅ Loaded GeoJSON: {GEOJSON_PATH}")
    return geojson_data
