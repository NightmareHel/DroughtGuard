# DroughtGuard Multi-Horizon Training Pipeline

This document explains how to train and deploy the DroughtGuard multi-horizon drought risk prediction models.

## Overview

DroughtGuard uses a **multi-horizon forecasting approach** to predict food insecurity risk 1, 2, and 3 months ahead. Each row in our dataset represents a (region, month) observation with recent environmental and market indicators. We train **three separate classifiers** for different prediction horizons:

- **Horizon 1 (h=1)**: Predicts risk 1 month ahead
- **Horizon 2 (h=2)**: Predicts risk 2 months ahead  
- **Horizon 3 (h=3)**: Predicts risk 3 months ahead

### Why Three Separate Models?

Different horizons require different feature importance and thresholds. For example:
- Short-term predictions (h=1) may rely more on recent rainfall anomalies
- Long-term predictions (h=3) may depend more on seasonal patterns and trend indicators

Each model is trained independently and calibrated to provide probability estimates for its specific horizon.

## Dataset Structure

Our dataset is structured as a **panel/time-series** where:
- **Rows**: (region, month) observations
- **Columns**: Current and recent values of environmental & market signals
- **Targets**: Risk status h months in the future (derived by shifting within each region)

### Example Data Structure
```
region,month,ndvi_anomaly,rainfall_anomaly,food_price_inflation,temp_anomaly,risk_label
Baringo,2023/01,-0.125,0.551,0.110,0.159,1
Baringo,2023/02,-0.344,-0.244,0.009,0.320,2
...
```

### Target Creation
- If explicit horizon targets exist (e.g., `y_h1`, `y_h2`, `y_h3`), they are used directly
- Otherwise, targets are derived by shifting the base target (`risk_label`) by +h months **within each region**
- This ensures **no data leakage**: features at time t predict labels at time t+h

## Setup Instructions

### First-Time Setup on Droplet

```bash
# Update system and install dependencies
apt update && apt install -y python3-pip python3-venv git

# Clone repository
git clone $GIT_REPO
cd DroughtGuard

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Set the following environment variables (replace with your actual values):

```bash
# DigitalOcean Spaces credentials
export SPACES_ACCESS_KEY="DO801GAW4PPQ7W632JL4"
export SPACES_SECRET_KEY="PlDMMjCCGiKDWCpl8nL2y3C6snHI9w8xZbY1LflB/d0"
export SPACES_REGION="nyc3"
export SPACES_BUCKET="droughtguardbucket"
export SPACES_ENDPOINT_URL="https://droughtguardbucket.nyc3.digitaloceanspaces.com"

# Training data path (optional - defaults to data/features.csv)
export TRAIN_DATA_PATH="data/features.csv"
```

## Training Pipeline

### 1. Run Training

```bash
# Activate virtual environment
source venv/bin/activate

# Run training pipeline
python model/train_pipeline.py
```

The training pipeline will:
1. **Validate dataset**: Check for duplicates, missing data, and target availability
2. **Engineer features**: Create lag features, seasonality, and differences
3. **Train models**: Train separate models for each horizon (h=1,2,3)
4. **Evaluate performance**: Use rolling-origin validation with metrics (ROC-AUC, Brier, Recall@FPR=0.2)
5. **Generate forecasts**: Create predictions for all regions and horizons
6. **Save artifacts**: Export models, metrics, and forecasts

### 2. Upload to DigitalOcean Spaces

```bash
# Upload all artifacts to Spaces
python model/upload_to_spaces.py
```

This will upload:
- Model files: `model_h1.pkl`, `model_h2.pkl`, `model_h3.pkl`
- Metrics: `metrics.json`
- Forecasts: `data/forecasts.csv`
- Upload manifest: `upload_manifest.json`

## Configuration

The training pipeline is configured via `model/config.yaml`. Key settings:

### Feature Engineering
```yaml
features:
  candidates: ["ndvi_anomaly", "rainfall_anomaly", "food_price_inflation", "temp_anomaly"]
  lags: [1, 2]  # Create x_t, x_t-1, x_t-2
  seasonality: true  # Add sin/cos month features
  diffs: true  # Add difference features (x_t - x_t-1)
```

### Risk Thresholds
```yaml
thresholds:
  h1: {red: 0.60, yellow: 0.35}
  h2: {red: 0.57, yellow: 0.33}
  h3: {red: 0.55, yellow: 0.30}
```

### Model Settings
```yaml
training:
  model_type: "xgboost"  # Falls back to "logreg" if XGBoost unavailable
  random_state: 42
  calibration: "isotonic"
  test_strategy: "rolling_origin"
```

## Output Files

### Models
- `model/model_h1.pkl`: 1-month horizon model
- `model/model_h2.pkl`: 2-month horizon model  
- `model/model_h3.pkl`: 3-month horizon model

### Forecasts
- `data/forecasts.csv`: Contains columns:
  - `region`: Region name
  - `date_current`: Latest observation date
  - `horizon`: Prediction horizon (1, 2, 3)
  - `prob`: Risk probability
  - `prob_lo`, `prob_hi`: Uncertainty bounds
  - `risk_level`: Categorized risk (Low/Moderate/High)
  - `model_version`: Training timestamp

### Metrics
- `model/metrics.json`: Performance metrics per horizon:
  - ROC-AUC
  - Brier Score
  - Recall at FPR=0.2

## DigitalOcean Spaces Structure

After upload, your Spaces bucket will contain:

```
droughtguardbucket/
├── models/
│   ├── model_h1_2025-01-26.pkl
│   ├── model_h2_2025-01-26.pkl
│   ├── model_h3_2025-01-26.pkl
│   ├── metrics_2025-01-26.json
│   └── upload_manifest.json
└── data/
    └── forecasts.csv
```

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   ```
   ERROR: Missing required environment variables!
   ```
   - Ensure all required environment variables are set
   - Check that credentials are correct

2. **Dataset Validation Errors**
   ```
   ValueError: Found X duplicate (region, date) combinations
   ```
   - Check for duplicate rows in your dataset
   - Ensure date column is properly formatted

3. **Missing Target Columns**
   ```
   ValueError: No target available for horizon X
   ```
   - Verify that either explicit `y_h1`, `y_h2`, `y_h3` columns exist
   - Or ensure `risk_label` column exists for target derivation

4. **XGBoost Import Error**
   ```
   XGBoost not available, falling back to LogisticRegression
   ```
   - Install XGBoost: `pip install xgboost`
   - Or use LogisticRegression (acceptable fallback)

5. **Insufficient Data**
   ```
   Dropped X rows with insufficient history
   ```
   - Ensure you have enough historical data for lag features
   - Consider reducing lag requirements in config

### Data Quality Checks

The pipeline performs several validation checks:

- **Duplicate Detection**: No duplicate (region, date) combinations
- **Date Monotonicity**: Dates increase within each region
- **Missing Data**: Warns if >20% missing in any column
- **Target Availability**: Ensures targets exist for all horizons

### Performance Monitoring

Monitor these metrics during training:

- **ROC-AUC**: Should be >0.6 for useful predictions
- **Brier Score**: Lower is better (0.25 = random, <0.2 = good)
- **Recall@FPR=0.2**: Should be >0.3 for early warning capability

## API Integration

The trained models and forecasts can be loaded by the Flask app:

```python
# Load forecasts
forecasts_df = pd.read_csv('data/forecasts.csv')

# Load models (if needed for real-time prediction)
import joblib
model_h1 = joblib.load('model/model_h1.pkl')
```

The app can then serve predictions via endpoints like `/region_data?h=1` using the risk categorization thresholds from the config.

## Maintenance

### Regular Retraining
- Retrain models monthly with new data
- Monitor performance metrics for degradation
- Update thresholds based on validation results

### Model Versioning
- Models are timestamped by default (`versioned_suffix: true`)
- Keep multiple versions for rollback capability
- Update app to use latest model versions

### Data Pipeline
- Ensure new data follows the same schema
- Validate data quality before training
- Monitor for concept drift in features