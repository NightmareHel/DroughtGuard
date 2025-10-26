"""
Prediction module for multi-horizon food insecurity risk forecasting.
"""
import joblib
import os
import numpy as np
from datetime import datetime
from typing import Dict, Optional, Union
from .utils.feature_validator import validate_features, normalize_features

# Load models and scalers for each horizon
models = {}
scalers = {}

for horizon in [1, 2, 3]:
    model_path = os.path.join('model', f'model_h{horizon}.pkl')
    scaler_path = os.path.join('model', f'scaler_h{horizon}.pkl')
    
    if os.path.exists(model_path) and os.path.exists(scaler_path):
        models[horizon] = joblib.load(model_path)
        scalers[horizon] = joblib.load(scaler_path)
    else:
        print(f"Warning: Model files for horizon {horizon} not found")

def prepare_features(raw_features):
    """
    Prepare feature array in correct format for model input.
    
    Args:
        raw_features (dict): Dictionary with current feature values
    
    Returns:
        array: Formatted feature array
    """
    # Extract month from the date
    current_month = datetime.strptime(raw_features['month'], '%Y/%m').month if 'month' in raw_features else datetime.now().month
    
    # Order features to match training data
    feature_array = np.array([
        raw_features.get('ndvi_anomaly_lag1', 0),
        raw_features.get('rainfall_anomaly_lag1', 0),
        raw_features.get('food_price_inflation_lag1', 0),
        raw_features.get('temp_anomaly_lag1', 0),
        raw_features.get('ndvi_anomaly_lag2', 0),
        raw_features.get('rainfall_anomaly_lag2', 0),
        raw_features.get('food_price_inflation_lag2', 0),
        raw_features.get('temp_anomaly_lag2', 0),
        current_month
    ]).reshape(1, -1)
    
    return feature_array

def predict_risk(features: Dict, horizon: Optional[int] = None) -> Union[float, Dict[int, float]]:
    """
    Predict food insecurity risk probability for specified horizon(s).
    
    Args:
        features (dict): Dictionary with feature values
        horizon (int, optional): Specific forecast horizon (1, 2, or 3 months ahead)
            If None, returns predictions for all horizons
    
    Returns:
        If horizon specified: float probability for that horizon
        If horizon=None: dict mapping horizon to probability
        
    Raises:
        ValueError: If features are invalid
    """
    # Validate features
    errors = validate_features(features)
    if errors:
        error_msg = "Invalid features:\n" + "\n".join(errors)
        raise ValueError(error_msg)
    
    # Normalize features
    features = normalize_features(features)
    
    if horizon is not None and horizon not in models:
        print(f"Warning: Model for horizon {horizon} not available")
        return 0.5
    
    feature_array = prepare_features(features)
    
    if horizon is not None:
        # Return probability for specific horizon
        if horizon not in models:
            return 0.5
        scaled_features = scalers[horizon].transform(feature_array)
        prob = float(models[horizon].predict_proba(scaled_features)[0][1])
        return round(prob, 3)  # Round to 3 decimal places for cleaner display
    
    # Return probabilities for all available horizons
    probabilities = {}
    for h in models.keys():
        scaled_features = scalers[h].transform(feature_array)
        prob = float(models[h].predict_proba(scaled_features)[0][1])
        probabilities[h] = round(prob, 3)
    
    return probabilities
