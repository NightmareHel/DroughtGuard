"""
Train a logistic regression model for food insecurity risk prediction.
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os

def train_model():
    """Train and save the logistic regression model."""
    
    # Load features
    data_path = os.path.join('..', 'data', 'features.csv')
    df = pd.read_csv(data_path)
    
    # Prepare features and target
    X = df[['ndvi_anomaly', 'rainfall_anomaly', 'food_price_inflation', 'temp_anomaly']]
    y = df['risk_label']  # Assuming binary: 0 = Low, 1 = High
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train model
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    train_score = model.score(X_train_scaled, y_train)
    test_score = model.score(X_test_scaled, y_test)
    
    print(f"Train Accuracy: {train_score:.4f}")
    print(f"Test Accuracy: {test_score:.4f}")
    
    # Save model and scaler
    model_path = os.path.join('.', 'model.pkl')
    scaler_path = os.path.join('.', 'scaler.pkl')
    
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    
    print(f"Model saved to {model_path}")
    print(f"Scaler saved to {scaler_path}")
    
    return model, scaler

if __name__ == '__main__':
    train_model()
