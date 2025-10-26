"""
Prediction module for food insecurity risk.
"""
import os
import joblib
import numpy as np

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
