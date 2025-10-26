"""
Train multiple models for different forecast horizons.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, brier_score_loss
import joblib
import os

def prepare_temporal_features(df, horizon):
    """
    Prepare features and target for a specific forecast horizon.
    
    Args:
        df (pd.DataFrame): Input dataframe with temporal data
        horizon (int): Forecast horizon (1, 2, or 3 months ahead)
        
    Returns:
        X (pd.DataFrame): Features
        y (pd.Series): Target labels
    """
    # Sort by region and time
    df = df.sort_values(['region', 'month'])
    
    # Create lagged features
    for col in ['ndvi_anomaly', 'rainfall_anomaly', 'food_price_inflation', 'temp_anomaly']:
        df[f'{col}_lag1'] = df.groupby('region')[col].shift(1)
        df[f'{col}_lag2'] = df.groupby('region')[col].shift(2)
    
    # Create future target (risk_label h months ahead)
    df[f'target_h{horizon}'] = df.groupby('region')['risk_label'].shift(-horizon)
    
    # Drop rows with NaN (first 2 months of each region and last h months)
    df = df.dropna()
    
    # Prepare feature matrix
    feature_cols = [col for col in df.columns if '_lag' in col]
    feature_cols += ['month']  # Include month as a feature
    
    # Convert month to numerical (assuming format YYYY/MM)
    df['month_num'] = pd.to_datetime(df['month']).dt.month
    
    X = df[feature_cols]
    y = df[f'target_h{horizon}']
    
    return X, y

def train_models():
    """Train and save models for each forecast horizon."""
    
    # Load features
    data_path = os.path.join('..', 'data', 'features.csv')
    df = pd.read_csv(data_path)
    
    # Train models for each horizon
    metrics = {}
    for horizon in [1, 2, 3]:
        print(f"\nTraining model for {horizon}-month horizon:")
        
        # Prepare features
        X, y = prepare_temporal_features(df, horizon)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False  # Keep temporal order
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model
        model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=3,
            random_state=42
        )
        model.fit(X_train_scaled, y_train)
        
        # Get probabilities
        train_probs = model.predict_proba(X_train_scaled)[:, 1]
        test_probs = model.predict_proba(X_test_scaled)[:, 1]
        
        # Calculate metrics
        metrics[f'h{horizon}'] = {
            'train_auc': roc_auc_score(y_train, train_probs),
            'test_auc': roc_auc_score(y_test, test_probs),
            'train_brier': brier_score_loss(y_train, train_probs),
            'test_brier': brier_score_loss(y_test, test_probs)
        }
        
        print(f"ROC-AUC (train/test): {metrics[f'h{horizon}']['train_auc']:.3f}/{metrics[f'h{horizon}']['test_auc']:.3f}")
        print(f"Brier Score (train/test): {metrics[f'h{horizon}']['train_brier']:.3f}/{metrics[f'h{horizon}']['test_brier']:.3f}")
        
        # Save model and scaler
        model_path = os.path.join('.', f'model_h{horizon}.pkl')
        scaler_path = os.path.join('.', f'scaler_h{horizon}.pkl')
        
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
    
    # Save metrics
    metrics_path = os.path.join('.', 'metrics.json')
    pd.DataFrame(metrics).to_json(metrics_path, indent=2)

if __name__ == '__main__':
    train_models()