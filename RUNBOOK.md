# DroughtGuard MLOps Runbook

## Quick Start Commands

### 1. Environment Variables to Set

```bash
# DigitalOcean Spaces credentials (REPLACE WITH YOUR ACTUAL VALUES)
export SPACES_ACCESS_KEY="DO801GAW4PPQ7W632JL4"
export SPACES_SECRET_KEY="PlDMMjCCGiKDWCpl8nL2y3C6snHI9w8xZbY1LflB/d0"
export SPACES_REGION="nyc3"
export SPACES_BUCKET="droughtguardbucket"
export SPACES_ENDPOINT_URL="https://droughtguardbucket.nyc3.digitaloceanspaces.com"

# Training data path (optional - defaults to data/features.csv)
export TRAIN_DATA_PATH="data/features.csv"
```

### 2. Commands to Run

```bash
# First time setup
apt update && apt install -y python3-pip python3-venv git
git clone $GIT_REPO
cd DroughtGuard
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Train models
python model/train_pipeline.py

# Upload to Spaces
python model/upload_to_spaces.py
```

### 3. Check Files in Spaces

Visit: https://cloud.digitalocean.com/spaces

Your bucket should contain:
- `models/model_h1_*.pkl` - 1-month horizon model
- `models/model_h2_*.pkl` - 2-month horizon model  
- `models/model_h3_*.pkl` - 3-month horizon model
- `models/metrics_*.json` - Performance metrics
- `data/forecasts.csv` - Generated forecasts
- `models/upload_manifest.json` - Upload details

### 4. Override CSV Path

If you rename your dataset file:

```bash
export TRAIN_DATA_PATH="path/to/your/updated_dataset.csv"
python model/train_pipeline.py
```

## What Each Component Does

### `model/config.yaml`
- Central configuration for all training parameters
- Feature engineering settings (lags, seasonality, diffs)
- Risk thresholds per horizon
- Model training parameters

### `model/data_checks.py`
- Validates dataset structure and quality
- Infers column names automatically
- Checks for duplicates, missing data, target availability
- Provides dataset summary

### `model/train_pipeline.py`
- Main training pipeline
- Creates features (lags, seasonality, differences)
- Trains separate models for h=1,2,3 horizons
- Generates forecasts for all regions
- Saves all artifacts

### `app/utils/categorizer.py`
- Maps probabilities to risk levels (Low/Moderate/High)
- Uses horizon-specific thresholds from config
- Provides color codes and icons for UI

### `model/upload_to_spaces.py`
- Uploads all artifacts to DigitalOcean Spaces
- Handles versioned filenames
- Creates upload manifest
- Provides public URLs

## Expected Outputs

### Training Output
```
DroughtGuard Multi-Horizon Training Pipeline
==================================================
Loaded configuration from model/config.yaml
Loading data from: data/features.csv
Loaded 1120 rows, 15 columns
...
TRAINING COMPLETE!
==================================================
Models trained for horizons: [1, 2, 3]
Features used: 25
Forecasts generated: 300

Horizon 1 metrics:
  roc_auc: 0.742
  brier: 0.189
  recall_at_fpr_0.2: 0.456
```

### Upload Output
```
DroughtGuard Artifact Upload to DigitalOcean Spaces
============================================================
Connecting to bucket: droughtguardbucket
Endpoint: https://droughtguardbucket.nyc3.digitaloceanspaces.com
[OK] Connected to DigitalOcean Spaces

Found 4 model files to upload

Uploading files...
[OK] model_h1_2025-01-26.pkl -> models/model_h1_2025-01-26.pkl
[OK] data/forecasts.csv -> data/forecasts.csv
...
Upload complete! (5 files uploaded)
```

## Troubleshooting

### Missing Dependencies
```bash
pip install xgboost PyYAML
```

### Dataset Issues
- Check CSV format and column names
- Ensure no duplicate (region, date) combinations
- Verify target columns exist

### Spaces Upload Issues
- Verify environment variables are set correctly
- Check bucket permissions
- Ensure endpoint URL is correct

### Model Performance Issues
- Check data quality and missing values
- Verify target distribution
- Consider adjusting thresholds in config

## File Structure After Training

```
DroughtGuard/
├── model/
│   ├── config.yaml
│   ├── data_checks.py
│   ├── train_pipeline.py
│   ├── upload_to_spaces.py
│   ├── model_h1_2025-01-26.pkl
│   ├── model_h2_2025-01-26.pkl
│   ├── model_h3_2025-01-26.pkl
│   ├── metrics_2025-01-26.json
│   └── upload_manifest.json
├── data/
│   ├── features.csv
│   └── forecasts.csv
└── app/utils/
    └── categorizer.py
```

## Next Steps

1. **Test the pipeline** with your dataset
2. **Monitor model performance** using the metrics
3. **Set up automated retraining** (monthly)
4. **Integrate with Flask app** to serve predictions
5. **Set up monitoring** for model drift and performance

## Support

- Check `model/README_training.md` for detailed documentation
- Review error messages for specific troubleshooting steps
- Ensure all environment variables are set correctly
- Verify dataset format matches expected schema
