"""
Utility functions for loading and validating DroughtGuard datasets and GeoJSON.
Supports dynamic path resolution even if run from Flask or a notebook.
"""

import os
import json
import pandas as pd

# --------------------------------------------------------------------
# PATH CONFIGURATION
# --------------------------------------------------------------------
# Dynamically locate the project root (handles imports from anywhere)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
GEO_DIR = os.path.join(PROJECT_ROOT, "app", "static", "geo")

FEATURES_PATH = os.path.join(DATA_DIR, "features.csv")
GEOJSON_PATH = os.path.join(GEO_DIR, "kenya.json")


# --------------------------------------------------------------------
# DATA LOADING
# --------------------------------------------------------------------
def load_features() -> pd.DataFrame:
    """Load and validate the feature dataset."""
    print(f"📂 Looking for features.csv in: {FEATURES_PATH}")

    if not os.path.exists(FEATURES_PATH):
        raise FileNotFoundError(f"❌ features.csv not found at {FEATURES_PATH}")

    try:
        df = pd.read_csv(FEATURES_PATH)
        print(f"✅ Loaded features from {FEATURES_PATH}")
    except Exception as e:
        raise RuntimeError(f"❌ Failed to load features.csv: {e}")

    print(f"📄 Columns found: {list(df.columns)}")

    # Expected columns
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

    # Clean data
    df = df.fillna(0)
    df["region"] = df["region"].astype(str)

    print(f"📊 Loaded {len(df)} records.")
    return df


# --------------------------------------------------------------------
# GEOJSON LOADING
# --------------------------------------------------------------------
def load_geojson() -> dict:
    """Load the Kenya GeoJSON file used for mapping regions."""
    print(f"📂 Looking for GeoJSON file in: {GEOJSON_PATH}")

    if not os.path.exists(GEOJSON_PATH):
        raise FileNotFoundError(f"❌ GeoJSON file not found at {GEOJSON_PATH}")

    try:
        with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)
        print(f"✅ Loaded GeoJSON: {GEOJSON_PATH}")
        print(f"🌍 Regions found: {len(geojson_data.get('features', []))}")
        return geojson_data

    except json.JSONDecodeError as e:
        raise ValueError(f"❌ Invalid GeoJSON format: {e}")
    except Exception as e:
        raise RuntimeError(f"❌ Failed to load GeoJSON: {e}")
