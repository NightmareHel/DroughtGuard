# Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 2. Train the Model

```bash
# Navigate to model directory
cd model

# Train the logistic regression model
python train_model.py

# This will create model.pkl and scaler.pkl files
```

### 3. Run the Application

```bash
# From the project root
cd app
python app.py

# Or alternatively:
cd ..
python app/app.py
```

### 4. Access the Application

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

## Next Steps

1. Add real Kenya GeoJSON data to `app/static/geo/kenya.json`
2. Update `data/features.csv` with real regional data
3. Customize the frontend styling in `app/static/style.css`
4. Add more features to the prediction model

## Troubleshooting

- If models don't load: Make sure you've run `train_model.py` first
- If map doesn't show: Check that GeoJSON file exists at `app/static/geo/kenya.json`
- If region data missing: Verify `data/features.csv` has the correct structure
