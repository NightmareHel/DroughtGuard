"""
Train logistic regression models for 1-, 2-, and 3-month-ahead
food insecurity risk forecasting for DroughtGuard.

This version assumes data/features.csv DOES NOT contain a 'month' column.
Each model uses exactly 4 features:
    ndvi_anomaly_lagX, rainfall_anomaly_lagX, food_price_inflation_lagX, temp_anomaly_lagX
…where X = 1 for h1, and X = 2 for h2/h3.
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# --------------------------------------------------------------------
# PATHS (anchored to project root regardless of where script runs)
# --------------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "features.csv")
MODEL_DIR = os.path.join(PROJECT_ROOT, "model")
os.makedirs(MODEL_DIR, exist_ok=True)

# --------------------------------------------------------------------
# UTIL
# --------------------------------------------------------------------
def _check_required_columns(df: pd.DataFrame, suffix: str) -> bool:
    req = [
        f"ndvi_anomaly_{suffix}",
        f"rainfall_anomaly_{suffix}",
        f"food_price_inflation_{suffix}",
        f"temp_anomaly_{suffix}",
    ]
    missing = [c for c in req if c not in df.columns]
    if missing:
        print(f"⚠️ Missing columns for {suffix}: {missing}")
        return False
    return True

def _make_Xy(df: pd.DataFrame, suffix: str):
    X = df[
        [
            f"ndvi_anomaly_{suffix}",
            f"rainfall_anomaly_{suffix}",
            f"food_price_inflation_{suffix}",
            f"temp_anomaly_{suffix}",
        ]
    ].copy()
    y = df["risk_label"].copy()

    # Clean bad values
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    y = y.fillna(0).astype(int)

    return X, y

# --------------------------------------------------------------------
# TRAIN ONE HORIZON
# --------------------------------------------------------------------
def train_horizon_model(df: pd.DataFrame, horizon: int, suffix: str):
    """Train LogisticRegression on 4 lag features for a given horizon."""
    print(f"\n📈 Training model for {horizon}-month horizon (using {suffix} features)…")

    if not _check_required_columns(df, suffix):
        print(f"⏭️ Skipping horizon {horizon} due to missing columns.")
        return

    X, y = _make_Xy(df, suffix)

    # Final sanity checks
    nan_total = X.isna().sum().sum()
    if nan_total:
        print(f"⚠️ NaNs detected in X before split: {nan_total} — filling with 0.")
        X = X.fillna(0.0)

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Scale all 4 numeric features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train.values)
    X_test_scaled = scaler.transform(X_test.values)

    # Final numeric sanitization (defensive)
    X_train_scaled = np.nan_to_num(X_train_scaled, nan=0.0, posinf=0.0, neginf=0.0)
    X_test_scaled = np.nan_to_num(X_test_scaled, nan=0.0, posinf=0.0, neginf=0.0)

    # Train
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X_train_scaled, y_train)

    # Evaluate
    train_acc = model.score(X_train_scaled, y_train)
    test_acc = model.score(X_test_scaled, y_test)
    print(f"✅ Horizon {horizon}: Train Acc = {train_acc:.3f} | Test Acc = {test_acc:.3f}")

    # Save
    model_path = os.path.join(MODEL_DIR, f"model_h{horizon}.pkl")
    scaler_path = os.path.join(MODEL_DIR, f"scaler_h{horizon}.pkl")
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    print(f"💾 Saved: {model_path}")
    print(f"💾 Saved: {scaler_path}")

# --------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------
def train_models():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"❌ Dataset not found at {DATA_PATH}")

    print(f"✅ Loading dataset from: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    print("📄 Columns found:", df.columns.tolist())

    # Horizon 1 (lag1)
    train_horizon_model(df, horizon=1, suffix="lag1")

    # Horizon 2 (lag2)
    train_horizon_model(df, horizon=2, suffix="lag2")

    # Horizon 3 (reuse lag2)
    train_horizon_model(df, horizon=3, suffix="lag2")

    print("\n🎉 Finished training available horizons.")
    print(f"📦 Artifacts in: {MODEL_DIR}")

if __name__ == "__main__":
    train_models()
