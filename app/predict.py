"""
Prediction module for food insecurity risk.
"""
import joblib
import os

# Load model and scaler
model_path = os.path.join('model', 'model.pkl')
scaler_path = os.path.join('model', 'scaler.pkl')

model = joblib.load(model_path) if os.path.exists(model_path) else None
scaler = joblib.load(scaler_path) if os.path.exists(scaler_path) else None

def predict_risk(features):
    """
    Predict food insecurity risk probability.
    
    Args:
        features (dict): Dictionary with keys:
            - ndvi_anomaly
            - rainfall_anomaly
            - food_price_inflation
    
    Returns:
        float: Risk probability (0-1)
    """
    if model is None or scaler is None:
        # Return mock prediction if model not loaded
        return 0.5
    
    # Convert features to array
    feature_array = [[
        features['ndvi_anomaly'],
        features['rainfall_anomaly'],
        features['food_price_inflation']
    ]]
    
    # Scale and predict
    scaled_features = scaler.transform(feature_array)
    probability = model.predict_proba(scaled_features)[0][1]
    
    return probability
