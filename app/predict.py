"""
Prediction module for multi-horizon food insecurity risk forecasting.
"""
import joblib
import os
import numpy as np
from datetime import datetime
from typing import Dict, Optional, Union
from utils.feature_validator import validate_features, normalize_features

# Load models for each horizon
models = {}

for horizon in [1, 2, 3]:
    # Try the new versioned models first, then fall back to old ones
    model_paths = [
        os.path.join('..', 'model', f'model_h{horizon}2025-10-26_03-15-50.pkl'),
        os.path.join('..', 'model', f'model_h{horizon}.pkl')
    ]
    
    model_loaded = False
    for model_path in model_paths:
        if os.path.exists(model_path):
            try:
                models[horizon] = joblib.load(model_path)
                print(f"[OK] Loaded model for horizon {horizon} from {model_path}")
                model_loaded = True
                break
            except Exception as e:
                print(f"[WARNING] Failed to load {model_path}: {e}")
                continue
    
    if not model_loaded:
        print(f"Warning: No model file found for horizon {horizon}")

def prepare_features(raw_features, use_old_format=False):
    """
    Prepare feature array in correct format for model input.
    
    Args:
        raw_features (dict): Dictionary with current feature values
        use_old_format (bool): If True, use 5-feature format for old models
    
    Returns:
        array: Formatted feature array
    """
    if use_old_format:
        # Old format: 5 features for legacy models
        feature_array = np.array([
            raw_features.get('ndvi_anomaly_lag1', 0),
            raw_features.get('rainfall_anomaly_lag1', 0),
            raw_features.get('food_price_inflation_lag1', 0),
            raw_features.get('temp_anomaly_lag1', 0),
            datetime.strptime(raw_features['month'], '%Y/%m').month if 'month' in raw_features else datetime.now().month
        ]).reshape(1, -1)
    else:
        # New format: 18 features for new models
        current_month = datetime.strptime(raw_features['month'], '%Y/%m').month if 'month' in raw_features else datetime.now().month
        
        # Create seasonality features
        sin_month = np.sin(2 * np.pi * current_month / 12)
        cos_month = np.cos(2 * np.pi * current_month / 12)
        
        # Calculate difference features
        ndvi_diff = raw_features.get('ndvi_anomaly', 0) - raw_features.get('ndvi_anomaly_lag1', 0)
        rainfall_diff = raw_features.get('rainfall_anomaly', 0) - raw_features.get('rainfall_anomaly_lag1', 0)
        price_diff = raw_features.get('food_price_inflation', 0) - raw_features.get('food_price_inflation_lag1', 0)
        temp_diff = raw_features.get('temp_anomaly', 0) - raw_features.get('temp_anomaly_lag1', 0)
        
        # Order features to match training data (18 features total)
        feature_array = np.array([
            raw_features.get('ndvi_anomaly', 0),
            raw_features.get('rainfall_anomaly', 0),
            raw_features.get('food_price_inflation', 0),
            raw_features.get('temp_anomaly', 0),
            raw_features.get('ndvi_anomaly_lag1', 0),
            raw_features.get('rainfall_anomaly_lag1', 0),
            raw_features.get('food_price_inflation_lag1', 0),
            raw_features.get('temp_anomaly_lag1', 0),
            raw_features.get('ndvi_anomaly_lag2', 0),
            raw_features.get('rainfall_anomaly_lag2', 0),
            raw_features.get('food_price_inflation_lag2', 0),
            raw_features.get('temp_anomaly_lag2', 0),
            sin_month,
            cos_month,
            ndvi_diff,
            rainfall_diff,
            price_diff,
            temp_diff
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
    
    # Determine which model format to use based on available models
    use_old_format = len(models) > 0 and hasattr(list(models.values())[0], 'n_features_in_') and list(models.values())[0].n_features_in_ == 5
    
    feature_array = prepare_features(features, use_old_format=use_old_format)
    
    if horizon is not None:
        # Return probability for specific horizon
        if horizon not in models:
            return 0.5
        prob = float(models[horizon].predict_proba(feature_array)[0][1])
        return round(prob, 3)  # Round to 3 decimal places for cleaner display
    
    # Return probabilities for all available horizons
    probabilities = {}
    for h in models.keys():
        prob = float(models[h].predict_proba(feature_array)[0][1])
        probabilities[h] = round(prob, 3)
    
    return probabilities
