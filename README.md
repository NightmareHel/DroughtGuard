# DroughtGuard

> AI-Driven Food Insecurity Early-Warning System for Kenya

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌍 Overview

**DroughtGuard** is an AI-driven early-warning system designed to monitor regional indicators of food insecurity in Kenya. By analyzing satellite vegetation health (NDVI), rainfall anomalies, and food price inflation, our system predicts areas at risk of crisis and helps humanitarian organizations prioritize early interventions.

**Team:** SentinelSight | **Hackathon:** 24-Hour Prototype | **Focus:** Humanitarian AI

## ✨ Key Features

- 📊 **Interactive Choropleth Map** — Visual representation of region-level food insecurity risk using LeafletJS
- 🎯 **Risk Prediction** — Logistic Regression model trained on regional features
- 💬 **Interactive Tooltips** — Hover over regions to view name and risk probability
- 🎨 **Color-Coded Risk Categories** — Green (Low), Yellow (Moderate), Red (High)
- 📈 **Feature Importance Visualization** — SHAP-style explainability charts
- 🔮 **Future Projections** — Optional "Next Month Projection" based on trend analysis
- 🎛️ **Region Selection Panel** — Sidebar for detailed insights and feature exploration

## 🛠️ Tech Stack

- **Backend:** Flask (Python)
- **Frontend:** HTML, CSS (Bootstrap), JavaScript (LeafletJS, Chart.js)
- **Model:** Logistic Regression (scikit-learn)
- **Data Sources:** NDVI anomalies, rainfall anomalies, food price inflation
- **Mapping:** GeoJSON with Kenya administrative boundaries
- **Deployment:** Render / localhost
- **Optional:** Google Earth Engine for real NDVI data

## 🏗️ Architecture Overview

```
User 
  ↓
Frontend (LeafletJS + HTML/CSS)
  ↓
Flask Backend (/predict API, Jinja templates)
  ↓
Model Engine (model.pkl, predict_risk)
  ↓
Data Store (features.csv, GeoJSON)
  ↓
Rendered Output → Interactive map + results panel
```

## 📁 Project Structure

```
DroughtGuard/
│
├─ app.py                    # Flask routes and logic
├─ model.pkl                 # Trained logistic regression model
├─ data/
│  ├─ features.csv          # NDVI, rainfall, price features by region
│  └─ kenya.geojson         # Admin-level map boundaries
├─ templates/
│  └─ index.html            # Main UI (Leaflet map + Jinja placeholders)
├─ static/
│  ├─ style.css             # Layout & color styling
│  ├─ script.js             # Map logic (Leaflet + tooltips)
│  └─ icons/                # Optional UI assets
├─ requirements.txt
└─ README.md
```

## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/DroughtGuard.git
   cd DroughtGuard
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run the Flask app:**
   ```bash
   python app.py
   ```

4. **Open your browser at:**
   ```
   http://127.0.0.1:5000
   ```

## 📖 Example Workflow

1. Select a region from the dropdown menu
2. Click **Predict** → backend fetches features, runs logistic regression, returns probability and risk label
3. The map updates with new color and tooltip text
4. Optionally, view the feature importance chart for explainability

## 🌐 Future Work

- 🔗 **Integrate Real Data** — Google Earth Engine for NDVI anomalies, rainfall SPI anomalies, and local market price APIs
- 🔄 **Automation** — Daily/weekly data updates
- 📧 **Alerts** — NGO notification system via email or dashboard
- 🌍 **Expansion** — Scale to multiple countries
- 🎯 **Model Improvements** — Deep learning models, ensemble methods
- 📊 **Advanced Analytics** — Time series forecasting, causal inference

## 🤝 Ethical Considerations

- **Privacy Protection** — Safe handling of regional risk predictions, avoid misuse
- **Transparency** — Communicate model uncertainty and limitations clearly
- **Inclusive Deployment** — Ensure context-aware and humanitarian-focused implementation
- **Bias Mitigation** — Regular validation and fairness checks on model outputs

## 👥 Authors

**Team SentinelSight**

- 📊 Data & Modeling — Person A
- 🔧 Backend API — Person B
- 🎨 Frontend & Mapping — Person C

## 📋 Judging Criteria Highlights

- **Problem Impact** — Addresses critical food insecurity challenges affecting vulnerable populations
- **Innovation** — AI-driven early-warning system with explainable predictions
- **Feasibility** — Demonstrated working prototype with clear deployment path
- **Technical Execution** — Clean architecture, scalable design, modern tech stack
- **Social Good** — Potential for humanitarian impact and NGO collaboration

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Contact

For questions, feedback, or collaboration opportunities, please open an issue on the GitHub repository.

---

**Built with ❤️ by Team SentinelSight in 24 hours**
