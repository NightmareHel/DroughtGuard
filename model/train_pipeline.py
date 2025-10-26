"""
Multi-horizon drought risk prediction training pipeline for DroughtGuard.
"""

import os
import sys
import yaml
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import warnings
import json

# Add model directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_checks import validate_dataset

# ML imports
from sklearn.model_selection import TimeSeriesSplit
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, brier_score_loss, roc_curve
from sklearn.preprocessing import StandardScaler
import joblib

# Try to import XGBoost, fallback to sklearn if not available
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("XGBoost not available, falling back to LogisticRegression")


def load_config(config_path: str = "model/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def create_lag_features(df: pd.DataFrame, feature_cols: List[str], lags: List[int], 
                       id_col: str, date_col: str) -> pd.DataFrame:
    """Create lag features for specified columns."""
    print(f"Creating lag features for {len(feature_cols)} columns with lags {lags}")
    
    df_work = df.copy()
    df_work = df_work.sort_values([id_col, date_col])
    
    new_features = []
    for col in feature_cols:
        if col in df_work.columns:
            for lag in lags:
                lag_col = f"{col}_lag{lag}"
                df_work[lag_col] = df_work.groupby(id_col)[col].shift(lag)
                new_features.append(lag_col)
    
    print(f"Created {len(new_features)} lag features")
    return df_work, new_features


def create_seasonality_features(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """Create seasonality features from date column."""
    print("Creating seasonality features")
    
    df_work = df.copy()
    dates = pd.to_datetime(df_work[date_col])
    
    # Extract month and create sin/cos features
    df_work['month'] = dates.dt.month
    df_work['sin_month'] = np.sin(2 * np.pi * df_work['month'] / 12)
    df_work['cos_month'] = np.cos(2 * np.pi * df_work['month'] / 12)
    
    print("Created sin_month, cos_month features")
    return df_work


def create_difference_features(df: pd.DataFrame, feature_cols: List[str], 
                             id_col: str, date_col: str) -> pd.DataFrame:
    """Create difference features (x_t - x_t-1) for specified columns."""
    print("Creating difference features")
    
    df_work = df.copy()
    df_work = df_work.sort_values([id_col, date_col])
    
    new_features = []
    for col in feature_cols:
        if col in df_work.columns:
            diff_col = f"{col}_diff"
            df_work[diff_col] = df_work.groupby(id_col)[col].diff()
            new_features.append(diff_col)
    
    print(f"Created {len(new_features)} difference features")
    return df_work, new_features


def create_targets(df: pd.DataFrame, horizons: List[int], available_targets: Dict[int, str],
                  id_col: str, date_col: str) -> pd.DataFrame:
    """Create target variables for each horizon."""
    print("Creating target variables for each horizon")
    
    df_work = df.copy()
    df_work = df_work.sort_values([id_col, date_col])
    
    for h in horizons:
        target_col = f"y_h{h}"
        
        if h in available_targets:
            explicit_col = available_targets[h]
            if explicit_col.startswith('y_h'):  # Already a horizon target
                df_work[target_col] = df_work[explicit_col]
            else:  # Base target, need to shift
                # Shift by -h so current row's label = future status at t+h
                df_work[target_col] = df_work.groupby(id_col)[explicit_col].shift(-h)
        else:
            raise ValueError(f"No target available for horizon {h}")
        
        # Convert to binary classification: 1 = high risk (2), 0 = low risk (1)
        # This maps risk_label values: 1 -> 0 (low risk), 2 -> 1 (high risk)
        df_work[target_col] = (df_work[target_col] == 2).astype(int)
    
    print(f"Created targets for horizons: {horizons}")
    return df_work


def prepare_features(df: pd.DataFrame, config: Dict[str, Any], 
                    id_col: str, date_col: str) -> Tuple[pd.DataFrame, List[str]]:
    """Prepare all features for training."""
    print("\n=== Feature Engineering ===")
    
    # Get feature candidates from config
    feature_candidates = config.get('features', {}).get('candidates', [])
    lags = config.get('features', {}).get('lags', [1, 2])
    
    # Find which candidates exist in the data
    existing_features = [col for col in feature_candidates if col in df.columns]
    print(f"Using {len(existing_features)} existing features: {existing_features}")
    
    df_work = df.copy()
    all_features = existing_features.copy()
    
    # Create lag features
    if lags:
        df_work, lag_features = create_lag_features(df_work, existing_features, lags, id_col, date_col)
        all_features.extend(lag_features)
    
    # Create seasonality features
    if config.get('features', {}).get('seasonality', True):
        df_work = create_seasonality_features(df_work, date_col)
        all_features.extend(['sin_month', 'cos_month'])
    
    # Create difference features
    if config.get('features', {}).get('diffs', True):
        df_work, diff_features = create_difference_features(df_work, existing_features, id_col, date_col)
        all_features.extend(diff_features)
    
    # Remove rows with insufficient history for lags
    if lags:
        max_lag = max(lags)
        initial_rows = len(df_work)
        df_work = df_work.dropna(subset=[f"{col}_lag{max_lag}" for col in existing_features if f"{col}_lag{max_lag}" in df_work.columns])
        print(f"Dropped {initial_rows - len(df_work)} rows with insufficient history")
    
    print(f"Final feature set: {len(all_features)} features")
    print(f"Final dataset shape: {df_work.shape}")
    
    return df_work, all_features


def rolling_origin_evaluation(df: pd.DataFrame, features: List[str], target_col: str,
                            id_col: str, date_col: str, model, config: Dict[str, Any]) -> Dict[str, float]:
    """Perform rolling origin evaluation."""
    print(f"\n=== Rolling Origin Evaluation for {target_col} ===")
    
    # Sort by date
    df_sorted = df.sort_values(date_col)
    unique_dates = sorted(df_sorted[date_col].unique())
    
    # Use last 20% of dates for testing
    n_test_dates = max(1, len(unique_dates) // 5)
    test_dates = unique_dates[-n_test_dates:]
    train_dates = unique_dates[:-n_test_dates]
    
    print(f"Training on {len(train_dates)} dates, testing on {len(test_dates)} dates")
    
    # Prepare training data
    train_mask = df_sorted[date_col].isin(train_dates)
    test_mask = df_sorted[date_col].isin(test_dates)
    
    X_train = df_sorted.loc[train_mask, features].fillna(0)
    y_train = df_sorted.loc[train_mask, target_col].fillna(0)
    X_test = df_sorted.loc[test_mask, features].fillna(0)
    y_test = df_sorted.loc[test_mask, target_col].fillna(0)
    
    print(f"Training set: {X_train.shape}, Test set: {X_test.shape}")
    
    # Train model
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Calculate metrics
    metrics = {}
    
    # ROC AUC
    if len(np.unique(y_test)) > 1:
        try:
            metrics['roc_auc'] = roc_auc_score(y_test, y_pred_proba)
        except ValueError:
            # Handle edge cases where ROC-AUC can't be computed
            metrics['roc_auc'] = 0.5
    else:
        metrics['roc_auc'] = 0.5
    
    # Brier score
    metrics['brier'] = brier_score_loss(y_test, y_pred_proba)
    
    # Recall at FPR = 0.2
    if len(np.unique(y_test)) > 1:
        try:
            fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)
            fpr_02_idx = np.argmin(np.abs(fpr - 0.2))
            metrics['recall_at_fpr_0.2'] = tpr[fpr_02_idx]
        except ValueError:
            # Handle edge cases where ROC curve can't be computed
            metrics['recall_at_fpr_0.2'] = 0.0
    else:
        metrics['recall_at_fpr_0.2'] = 0.0
    
    print(f"Metrics: {metrics}")
    return metrics


def create_model(config: Dict[str, Any]) -> Any:
    """Create model based on configuration."""
    model_type = config.get('training', {}).get('model_type', 'xgboost')
    random_state = config.get('training', {}).get('random_state', 42)
    
    if model_type == 'xgboost' and XGBOOST_AVAILABLE:
        model = xgb.XGBClassifier(
            random_state=random_state,
            eval_metric='logloss',
        n_estimators=100,
            max_depth=6,
            learning_rate=0.1
        )
        print("Using XGBoost classifier")
    else:
        model = LogisticRegression(
            random_state=random_state,
            class_weight=config.get('training', {}).get('class_weight', 'balanced'),
            max_iter=1000
        )
        print("Using LogisticRegression classifier")
    
    return model


def train_horizon_model(df: pd.DataFrame, features: List[str], horizon: int,
                       id_col: str, date_col: str, config: Dict[str, Any]) -> Tuple[Any, Dict[str, float]]:
    """Train model for a specific horizon."""
    print(f"\n{'='*50}")
    print(f"TRAINING MODEL FOR HORIZON {horizon}")
    print(f"{'='*50}")
    
    target_col = f"y_h{horizon}"
    
    # Check if target exists
    if target_col not in df.columns:
        raise ValueError(f"Target column {target_col} not found")
    
    # Remove rows with missing targets
    df_clean = df.dropna(subset=[target_col])
    print(f"Using {len(df_clean)} rows with valid targets")
    
    # Create model
    model = create_model(config)
    
    # Perform evaluation
    metrics = rolling_origin_evaluation(df_clean, features, target_col, id_col, date_col, model, config)
    
    # Train final model on all available data
    X_final = df_clean[features].fillna(0)
    y_final = df_clean[target_col].fillna(0)
    
    print(f"Training final model on {X_final.shape[0]} samples")
    model.fit(X_final, y_final)
    
    # Apply calibration if specified
    calibration = config.get('training', {}).get('calibration')
    if calibration == 'isotonic':
        print("Applying isotonic calibration")
        calibrated_model = CalibratedClassifierCV(model, method='isotonic', cv=3)
        calibrated_model.fit(X_final, y_final)
        model = calibrated_model
    
    return model, metrics


def generate_forecasts(df: pd.DataFrame, models: Dict[int, Any], features: List[str],
                      id_col: str, date_col: str, config: Dict[str, Any]) -> pd.DataFrame:
    """Generate forecasts for all regions and horizons."""
    print("\n=== Generating Forecasts ===")
    
    # Get the latest date for each region
    latest_data = df.groupby(id_col).tail(1).copy()
    print(f"Generating forecasts for {len(latest_data)} regions")
    
    forecasts = []
    horizons = config.get('targets', {}).get('horizons', [1, 2, 3])
    
    for _, row in latest_data.iterrows():
        region = row[id_col]
        current_date = row[date_col]
        
        # Prepare features for this region
        X = row[features].fillna(0).values.reshape(1, -1)
        
        for h in horizons:
            if h in models:
                model = models[h]
                
                # Get probability prediction
                prob = model.predict_proba(X)[0, 1]
                
                # Simple uncertainty estimation (could be improved with bootstrap)
                prob_lo = max(0, prob - 0.1)
                prob_hi = min(1, prob + 0.1)
                
                # Determine risk level based on thresholds
                thresholds = config.get('thresholds', {}).get(f'h{h}', {})
                red_thresh = thresholds.get('red', 0.6)
                yellow_thresh = thresholds.get('yellow', 0.35)
                
                if prob >= red_thresh:
                    risk_level = 'High'
                elif prob >= yellow_thresh:
                    risk_level = 'Moderate'
                else:
                    risk_level = 'Low'
            
            forecasts.append({
                'region': region,
                    'date_current': current_date,
                    'horizon': h,
                    'prob': prob,
                    'prob_lo': prob_lo,
                    'prob_hi': prob_hi,
                    'risk_level': risk_level,
                    'model_version': datetime.now().strftime('%Y-%m-%d')
                })
    
    forecasts_df = pd.DataFrame(forecasts)
    print(f"Generated {len(forecasts_df)} forecasts")
    
    return forecasts_df


def save_artifacts(models: Dict[int, Any], metrics: Dict[int, Dict[str, float]], 
                  forecasts_df: pd.DataFrame, features: List[str], config: Dict[str, Any]) -> None:
    """Save all training artifacts."""
    print("\n=== Saving Artifacts ===")
    
    # Create output directories
    models_dir = config.get('export', {}).get('out_models_dir', 'model')
    data_dir = config.get('export', {}).get('out_data_dir', 'data')
    
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    
    # Save models
    versioned = config.get('export', {}).get('versioned_suffix', True)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S') if versioned else ''
    
    for h, model in models.items():
        model_path = os.path.join(models_dir, f'model_h{h}{timestamp}.pkl')
        joblib.dump(model, model_path)
        print(f"Saved model for horizon {h}: {model_path}")
    
    # Save metrics
    metrics_path = os.path.join(models_dir, f'metrics{timestamp}.json')
    metrics_data = {
        'timestamp': datetime.now().isoformat(),
        'features_used': features,
        'horizons': {}
    }
    
    for h, h_metrics in metrics.items():
        metrics_data['horizons'][f'h{h}'] = h_metrics
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics_data, f, indent=2)
    print(f"Saved metrics: {metrics_path}")
    
    # Save forecasts
    forecasts_path = os.path.join(data_dir, 'forecasts.csv')
    forecasts_df.to_csv(forecasts_path, index=False)
    print(f"Saved forecasts: {forecasts_path}")


def main():
    """Main training pipeline."""
    print("DroughtGuard Multi-Horizon Training Pipeline")
    print("=" * 50)
    
    # Load configuration
    config = load_config()
    print(f"Loaded configuration from model/config.yaml")
    
    # Validate dataset
    df, id_col, date_col, available_targets = validate_dataset(config=config)
    
    # Prepare features
    df_features, features = prepare_features(df, config, id_col, date_col)
    
    # Create targets
    horizons = config.get('targets', {}).get('horizons', [1, 2, 3])
    df_final = create_targets(df_features, horizons, available_targets, id_col, date_col)
    
    # Train models for each horizon
    models = {}
    all_metrics = {}
    
    for h in horizons:
        model, metrics = train_horizon_model(df_final, features, h, id_col, date_col, config)
        models[h] = model
        all_metrics[h] = metrics
    
    # Generate forecasts
    forecasts_df = generate_forecasts(df_final, models, features, id_col, date_col, config)
    
    # Save all artifacts
    save_artifacts(models, all_metrics, forecasts_df, features, config)
    
    print("\n" + "=" * 50)
    print("TRAINING COMPLETE!")
    print("=" * 50)
    print(f"Models trained for horizons: {list(models.keys())}")
    print(f"Features used: {len(features)}")
    print(f"Forecasts generated: {len(forecasts_df)}")
    
    # Print summary metrics
    for h, metrics in all_metrics.items():
        print(f"\nHorizon {h} metrics:")
        for metric, value in metrics.items():
            print(f"  {metric}: {value:.3f}")


if __name__ == "__main__":
    main()