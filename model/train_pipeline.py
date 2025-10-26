"""
DroughtGuard Training Pipeline
Trains multiple horizon models and exports artifacts.
"""
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib

# Configuration
DATA_PATH = os.path.join('..', 'data', 'features.csv')
OUTPUT_DIR = '.'
HORIZONS = [1, 2, 3]  # Forecast horizons in months


def load_data():
    """Load and prepare training data."""
    print(f"Loading data from {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    
    # Feature engineering
    df['month_num'] = pd.to_datetime(df['month'], format='%Y/%m').dt.month
    df['year'] = pd.to_datetime(df['month'], format='%Y/%m').dt.year
    
    print(f"   Loaded {len(df)} rows, {len(df.columns)} columns")
    print(f"   Regions: {df['region'].unique()}")
    print(f"   Date range: {df['month'].min()} to {df['month'].max()}")
    
    return df


def prepare_features(df):
    """Prepare features for training."""
    feature_cols = [
        'ndvi_anomaly', 'rainfall_anomaly', 'food_price_inflation', 
        'temp_anomaly', 'month_num'
    ]
    
    X = df[feature_cols].values
    y = df['risk_label'].values
    
    return X, y


def train_horizon_model(X, y, horizon):
    """Train a model for a specific forecast horizon."""
    print(f"\nTraining Horizon {horizon} Model...")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42 + horizon
    )
    
    # Train model
    model = GradientBoostingClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
    
    print(f"   Accuracy: {accuracy:.4f}")
    print(f"   Precision: {precision:.4f}")
    print(f"   Recall: {recall:.4f}")
    print(f"   F1 Score: {f1:.4f}")
    
    metrics = {
        'horizon': horizon,
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'n_samples_train': len(X_train),
        'n_samples_test': len(X_test)
    }
    
    return model, metrics


def generate_forecasts(df, models):
    """Generate forecasts for future periods."""
    print(f"\nGenerating forecasts...")
    
    # Get latest data point for each region
    latest = df.sort_values('month').groupby('region').tail(1)
    
    forecasts = []
    for _, row in latest.iterrows():
        region = row['region']
        base_features = np.array([[
            row['ndvi_anomaly'],
            row['rainfall_anomaly'],
            row['food_price_inflation'],
            row['temp_anomaly'],
            row['month_num']
        ]])
        
        for horizon in HORIZONS:
            # Predict using horizon-specific model
            model = models[horizon]
            pred = model.predict(base_features)[0]
            proba = model.predict_proba(base_features)[0]
            
            forecasts.append({
                'region': region,
                'horizon': horizon,
                'predicted_risk': int(pred),
                'prob_low': float(proba[0]) if len(proba) > 0 else 0.0,
                'prob_moderate': float(proba[1]) if len(proba) > 1 else 0.0,
                'prob_high': float(proba[2]) if len(proba) > 2 else 0.0,
                'forecast_date': datetime.now().strftime('%Y-%m-%d')
            })
    
    forecast_df = pd.DataFrame(forecasts)
    
    print(f"   Generated {len(forecast_df)} forecasts across {len(df['region'].unique())} regions")
    
    return forecast_df


def main():
    """Main training pipeline."""
    print("=" * 60)
    print("DroughtGuard Model Training Pipeline")
    print("=" * 60)
    
    # Load data
    df = load_data()
    X, y = prepare_features(df)
    
    # Train models for each horizon
    models = {}
    all_metrics = []
    
    for horizon in HORIZONS:
        model, metrics = train_horizon_model(X, y, horizon)
        models[horizon] = model
        all_metrics.append(metrics)
        
        # Save model
        model_path = os.path.join(OUTPUT_DIR, f'model_h{horizon}.pkl')
        joblib.dump(model, model_path)
        print(f"   Saved: {model_path}")
    
    # Generate forecasts
    forecast_df = generate_forecasts(df, models)
    
    # Save forecasts
    forecast_path = os.path.join('..', 'data', 'forecasts.csv')
    forecast_df.to_csv(forecast_path, index=False)
    print(f"   Saved: {forecast_path}")
    
    # Save metrics
    metrics_path = os.path.join(OUTPUT_DIR, 'metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump({
            'training_date': datetime.now().isoformat(),
            'n_samples': len(df),
            'n_regions': len(df['region'].unique()),
            'models': all_metrics
        }, f, indent=2)
    print(f"   Saved: {metrics_path}")
    
    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)
    print("\nNext step: Run upload_to_spaces.py to upload artifacts to DigitalOcean Spaces")


if __name__ == '__main__':
    main()
