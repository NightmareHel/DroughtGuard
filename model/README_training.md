# DroughtGuard Training Pipeline - Deployment Guide

## Overview

This guide walks you through training and deploying DroughtGuard models on your DigitalOcean Droplet.

## Prerequisites

- Ubuntu 22.04 Droplet
- Python 3.11 installed
- DigitalOcean Spaces bucket created
- SSH access to your Droplet

## Step 1: Clone Repository on Droplet

```bash
# SSH into your Droplet
ssh root@your-droplet-ip

# Clone the repository
git clone https://github.com/yourusername/DroughtGuard.git
cd DroughtGuard

# Install dependencies
pip3 install -r requirements.txt
pip3 install boto3  # For Spaces upload
```

## Step 2: Configure Environment Variables

Create a `.env` file in the project root:

```bash
nano .env
```

Add your DigitalOcean Spaces credentials:

```bash
SPACES_ACCESS_KEY=DO8013VCV2KYKHR7V8DH
SPACES_SECRET_KEY=LIHmKADVJvvfgVJ91gpKk0QGQsMvRtF3cSHtRciWUxM
SPACES_REGION=nyc3
SPACES_BUCKET=droughtguard-models
```

**Security**: Never commit the `.env` file to Git! Add it to `.gitignore`.

## Step 3: Load Environment Variables

For the current session:
```bash
export $(cat .env | xargs)
```

To make permanent, add to your shell profile:
```bash
echo "export $(cat .env | xargs)" >> ~/.bashrc
source ~/.bashrc
```

Verify the variables are loaded:
```bash
echo $SPACES_ACCESS_KEY
```

## Step 4: Run Training Pipeline

Navigate to the model directory and run training:

```bash
cd model/
python3 train_pipeline.py
```

**Expected Output:**
```
============================================================
🌍 DroughtGuard Model Training Pipeline
============================================================
📊 Loading data from ../data/features.csv
   Loaded 242 rows, 7 columns
   Regions: ['Nairobi' 'Mombasa' 'Kisumu' ...]
   Date range: 2023/01 to 2024/12

🔮 Training Horizon 1 Model...
   Accuracy: 0.8542
   Precision: 0.8500
   Recall: 0.8542
   F1 Score: 0.8500
   💾 Saved: ./model_h1.pkl

🔮 Training Horizon 2 Model...
   ...

📈 Generating forecasts...
   Generated 15 forecasts across 5 regions
   💾 Saved: ../data/forecasts.csv

💾 Saved: ./metrics.json

============================================================
✅ Training complete!
============================================================
```

## Step 5: Upload Artifacts to DigitalOcean Spaces

```bash
python3 upload_to_spaces.py
```

**Expected Output:**
```
============================================================
☁️  DroughtGuard Artifact Upload to DigitalOcean Spaces
============================================================

🔐 Connecting to bucket: droughtguard-models (region: nyc3)
   ✅ Connected to DigitalOcean Spaces

📤 Uploading files...
   ✅ model_h1.pkl -> models/model_h1.pkl
      📎 https://nyc3.digitaloceanspaces.com/droughtguard-models/models/model_h1.pkl
   ✅ model_h2.pkl -> models/model_h2.pkl
      📎 https://nyc3.digitaloceanspaces.com/droughtguard-models/models/model_h2.pkl
   ...

============================================================
✅ Upload complete! (5/5 files)
============================================================

📋 Verification:
   Visit: https://cloud.digitalocean.com/spaces
   Bucket: droughtguard-models
```

## Step 6: Verify Uploads

### Option 1: DigitalOcean Console
1. Visit https://cloud.digitalocean.com/spaces
2. Click on your `droughtguard-models` bucket
3. You should see:
   - `models/` folder with `model_h1.pkl`, `model_h2.pkl`, `model_h3.pkl`, `metrics.json`
   - `data/` folder with `forecasts.csv`

### Option 2: Direct URLs
Access files directly via public URLs:
```
https://nyc3.digitaloceanspaces.com/droughtguard-models/models/model_h1.pkl
https://nyc3.digitaloceanspaces.com/droughtguard-models/data/forecasts.csv
```

## Automated Pipeline (Optional)

Create a cron job to run training weekly:

```bash
# Edit crontab
crontab -e

# Add this line (runs every Monday at 2 AM)
0 2 * * 1 cd /root/DroughtGuard && export $(cat .env | xargs) && cd model && python3 train_pipeline.py && python3 upload_to_spaces.py >> /var/log/droughtguard_training.log 2>&1
```

## Troubleshooting

### Error: "Missing required environment variables"
- Check that `.env` file exists
- Verify you exported variables: `echo $SPACES_ACCESS_KEY`

### Error: "Access Denied" when uploading
- Verify your Spaces credentials
- Check bucket name matches exactly
- Ensure the bucket exists in the correct region

### Error: "boto3 not found"
```bash
pip3 install boto3
```

### Model files not found
Make sure you run `train_pipeline.py` before `upload_to_spaces.py`

## File Structure After Training

```
DroughtGuard/
├── model/
│   ├── model_h1.pkl      # Horizon 1 model
│   ├── model_h2.pkl      # Horizon 2 model
│   ├── model_h3.pkl      # Horizon 3 model
│   ├── metrics.json      # Training metrics
│   ├── train_pipeline.py # Training script
│   └── upload_to_spaces.py # Upload script
└── data/
    ├── features.csv      # Training data (source)
    └── forecasts.csv     # Generated forecasts
```

## Next Steps

1. **Integration**: Update your Flask app to download models from Spaces
2. **Monitoring**: Set up alerts for training failures
3. **A/B Testing**: Compare model versions using metrics.json
4. **Automation**: Schedule regular re-training with new data

## Support

For issues or questions:
- Check logs: `/var/log/droughtguard_training.log` (if using cron)
- Review metrics: `model/metrics.json`
- DigitalOcean Spaces docs: https://docs.digitalocean.com/products/spaces/
