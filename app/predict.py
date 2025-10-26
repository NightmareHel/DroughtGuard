"""
<<<<<<< Updated upstream
Prediction module for food insecurity risk.
"""
=======
Prediction module for DroughtGuard multi-horizon food-insecurity forecasting.

Each model uses exactly four lag features:
    ndvi_anomaly_lagX, rainfall_anomaly_lagX,
    food_price_inflation_lagX, temp_anomaly_lagX
where X = 1 for 1-month ahead, 2 for 2- and 3-month ahead.
"""

>>>>>>> Stashed changes
import os
import joblib
import numpy as np

<<<<<<< Updated upstream
# 🔹 Step 1: set up base directory (root of your project)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# 🔹 Step 2: define model and scaler paths
MODEL_PATH = os.path.join(BASE_DIR, 'model', 'model.pkl')
SCALER_PATH = os.path.join(BASE_DIR, 'model', 'scaler.pkl')

# 🔹 Step 3: load them ONCE when this file imports (global scope)
try:
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    print(f"✅ Model loaded from: {MODEL_PATH}")
    print(f"✅ Scaler loaded from: {SCALER_PATH}")
except Exception as e:
    print(f"⚠️ Could not load model/scaler: {e}")
    model, scaler = None, None

# 🔹 Step 4: define the function
def predict_risk(features):
    """Predict food insecurity risk probability."""
    if model is None or scaler is None:
        print("⚠️ Model or scaler not loaded — returning fallback 0.2")
        return 0.2

    try:
        feature_array = [[
            float(features['ndvi_anomaly']),
            float(features['rainfall_anomaly']),
            float(features['food_price_inflation']),
            float(features['temp_anomaly'])
        ]]
    except KeyError as e:
        print(f"❌ Missing key: {e}")
        return 0.2

    scaled = scaler.transform(feature_array)
    probability = float(model.predict_proba(scaled)[0][1])
    print(f"🎯 Predicted probability: {probability:.3f}")
    return probability
=======
# --------------------------------------------------------------------
# PATHS
# --------------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
MODEL_DIR = os.path.join(PROJECT_ROOT, "model")

# --------------------------------------------------------------------
# LOAD MODELS + SCALERS
# --------------------------------------------------------------------
def _safe_load(path):
    try:
        return joblib.load(path)
    except Exception as e:
        print(f"⚠️ Could not load {path}: {e}")
        return None

models = {
    "h1": _safe_load(os.path.join(MODEL_DIR, "model_h1.pkl")),
    "h2": _safe_load(os.path.join(MODEL_DIR, "model_h2.pkl")),
    "h3": _safe_load(os.path.join(MODEL_DIR, "model_h3.pkl")),
}

scalers = {
    "h1": _safe_load(os.path.join(MODEL_DIR, "scaler_h1.pkl")),
    "h2": _safe_load(os.path.join(MODEL_DIR, "scaler_h2.pkl")),
    "h3": _safe_load(os.path.join(MODEL_DIR, "scaler_h3.pkl")),
}

# --------------------------------------------------------------------
# FEATURE VECTOR BUILDER
# --------------------------------------------------------------------
def build_feature_vector(region_data: dict, lag_type: str) -> np.ndarray:
    """Construct the 4-feature array expected by each model."""
    lag_cols = [
        f"ndvi_anomaly_{lag_type}",
        f"rainfall_anomaly_{lag_type}",
        f"food_price_inflation_{lag_type}",
        f"temp_anomaly_{lag_type}",
    ]
    values = [float(region_data.get(col, 0.0)) for col in lag_cols]
    return np.array([values], dtype=float)

# --------------------------------------------------------------------
# MAIN PREDICTION FUNCTION
# --------------------------------------------------------------------
def predict_risk(region_features: dict) -> dict:
    """
    Returns a dict of probabilities for each horizon:
        { "1_month": p1, "2_month": p2, "3_month": p3 }
    """
    results = {}

    for key, lag_type in zip(["h1", "h2", "h3"], ["lag1", "lag2", "lag2"]):
        model = models.get(key)
        scaler = scalers.get(key)

        if model is None or scaler is None:
            print(f"⚠️ Model or scaler missing for {key}")
            continue

        X = build_feature_vector(region_features, lag_type)

        try:
            X_scaled = scaler.transform(X)
        except Exception as e:
            print(f"⚠️ Scaling error for {key}: {e}")
            X_scaled = X  # fallback (unscaled)

        try:
            proba = float(model.predict_proba(X_scaled)[0][1])
        except Exception as e:
            print(f"❌ Prediction error for {key}: {e}")
            proba = 0.0

        results[f"{key.replace('h', '')}_month"] = round(proba, 3)

    # Fallback if nothing predicted
    if not results:
        results = {"1_month": 0.2}

    return results
>>>>>>> Stashed changes
