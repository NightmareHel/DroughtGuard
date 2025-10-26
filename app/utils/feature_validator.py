"""
Feature validation utilities for drought prediction.
"""
from typing import Dict, List, Optional
from datetime import datetime

REQUIRED_FEATURES = {
    'ndvi_anomaly': float,
    'rainfall_anomaly': float,
    'food_price_inflation': float,
    'temp_anomaly': float,
    'ndvi_anomaly_lag1': float,
    'rainfall_anomaly_lag1': float,
    'food_price_inflation_lag1': float,
    'temp_anomaly_lag1': float,
    'ndvi_anomaly_lag2': float,
    'rainfall_anomaly_lag2': float,
    'food_price_inflation_lag2': float,
    'temp_anomaly_lag2': float,
    'month': str  # Format: YYYY/MM
}

def validate_features(features: Dict) -> List[str]:
    """
    Validate input features for prediction.
    
    Args:
        features (dict): Input feature dictionary
        
    Returns:
        list: List of validation error messages. Empty if valid.
    """
    errors = []
    
    # Check for required features
    for feature, expected_type in REQUIRED_FEATURES.items():
        if feature not in features:
            errors.append(f"Missing required feature: {feature}")
            continue
            
        value = features[feature]
        
        # Handle month format specially
        if feature == 'month':
            try:
                datetime.strptime(value, '%Y/%m')
            except ValueError:
                errors.append(f"Invalid month format for {feature}. Expected YYYY/MM, got {value}")
            continue
            
        # Type checking for numerical features
        try:
            float(value)  # All our features should be convertible to float
        except (TypeError, ValueError):
            errors.append(f"Invalid type for {feature}. Expected {expected_type.__name__}, got {type(value).__name__}")
            
        # Range validation for anomalies
        if '_anomaly' in feature and isinstance(value, (int, float)):
            if not -5 <= float(value) <= 5:
                errors.append(f"Value out of expected range for {feature}: {value} (expected between -5 and 5)")
                
    return errors

def normalize_features(features: Dict) -> Dict:
    """
    Normalize feature values, converting strings to appropriate types.
    
    Args:
        features (dict): Raw feature dictionary
        
    Returns:
        dict: Normalized feature dictionary
    """
    normalized = {}
    
    for feature, value in features.items():
        if feature == 'month':
            normalized[feature] = str(value)
        else:
            try:
                normalized[feature] = float(value)
            except (TypeError, ValueError):
                normalized[feature] = 0.0  # Default for invalid values
                
    return normalized