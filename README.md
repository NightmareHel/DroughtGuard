# DroughtGuard

> ⚠️ **Fork Notice**
>
> This repository is a fork of the original DroughtGuard hackathon project:
> https://github.com/ORIGINAL_OWNER/DroughtGuard  
>
> Built as a **team project** during a 24-hour hackathon.
>

> AI-Driven Food Insecurity Early-Warning System for Kenya

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

🧠 Overview

DroughtGuard is an AI-powered early-warning and advisory system that predicts food insecurity risks across Kenya up to three months in advance.
It integrates environmental, climatic, and market indicators to help humanitarian agencies, governments, and NGOs act proactively before crises occur.

The system visualizes regional risk levels on an interactive choropleth map, powered by real or simulated data on:

NDVI (Normalized Difference Vegetation Index) anomalies

Rainfall anomalies

Temperature anomalies

Food price inflation

Focus: Humanitarian AI & Early Warning Systems
Team: SentinelSight
Built for: Hackathon (24-hour prototype)

✨ Key Features

🗺️ Interactive Choropleth Map — Region-level visualization of drought and food insecurity risk.

🔮 Multi-Horizon Risk Forecasts — Predictions for 1, 2, and 3 months ahead using pre-trained ML models.

⚙️ AI Advisor (Gemini Integration) — Optional AI summaries and context-aware briefs for analysts.

📊 Region Dashboard Panel — View forecasts, risk probabilities, and trend-based insights.

🧩 Modular Design — ML prediction and AI advisor components are independent and swappable.

🎨 Thematic UI — Modern Andromeda-style dark dashboard with gray basemap and color-coded risk levels.

🧠 Explainable Predictions — Human-readable risk categories (Low, Moderate, High).

🚀 Cloud-Ready Deployment — Tested on Vultr with .tech domain hosting.

🏗️ Tech Stack
Layer	Technology
Frontend	HTML, CSS, JavaScript (LeafletJS, Chart.js)
Backend	Flask (Python)
Machine Learning	Scikit-learn Gradient Boosting Classifier
LLM Integration	Google Gemini via google-generativeai (optional)
Data Storage	CSV (synthetic regional features), GeoJSON (Kenya counties)
Environment Management	Python-dotenv
Hosting	Vultr (Ubuntu 22.04)
Version Control	GitHub
🧩 Architecture Overview
User 
  ↓
Frontend (LeafletJS + Sidebar Dashboard)
  ↓
Flask API Backend
  ├─ /api/predict          → Model-based risk forecasts
  ├─ /api/brief/<region>   → AI-generated summaries (Gemini)
  ├─ /api/map-data         → GeoJSON features for map
  ├─ /api/regions          → Region name list
  ↓
Model Engine (model.pkl, scaler.pkl)
  ↓
Data Layer (features.csv, kenya.json)
  ↓
Rendered Output → Interactive dashboard + AI brief

📁 Project Structure
DroughtGuard/
│
├─ app/
│  ├─ app.py                     # Main Flask entry point
│  ├─ predict.py                 # Risk model logic
│  ├─ utils/
│  │   ├─ data_loader.py         # Load features & GeoJSON
│  │   ├─ categorizer.py         # Risk categorization helper
│  │   ├─ llm_chain.py           # Gemini AI advisor logic
│  │   └─ ai_cache.py            # In-memory AI response cache
│  ├─ templates/
│  │   ├─ base.html
│  │   ├─ index.html             # Main dashboard
│  │   └─ region.html
│  └─ static/
│      ├─ geo/kenya.json         # Kenya region boundaries
│      ├─ style.css              # Dashboard theme + sidebar scroll
│      └─ script.js              # Map logic, fetch calls, AI brief rendering
│
├─ data/
│   ├─ features.csv              # Synthetic dataset (regional indicators)
│   └─ mock_data_notes.md
│
├─ model/
│   ├─ model.pkl                 # ML model for current horizon
│   ├─ model_h1.pkl/h2.pkl/h3.pkl
│   ├─ scaler.pkl                # Feature normalization
│   └─ train_multi_horizon.py    # Training script
│
├─ requirements.txt
├─ .env                          # Environment variables (Flask & Gemini)
└─ README.md

🧠 Installation
1️⃣ Clone the Repository
git clone https://github.com/yourusername/DroughtGuard.git
cd DroughtGuard

2️⃣ Create a Virtual Environment
python -m venv venv
# Activate
venv\Scripts\activate  # (Windows)
source venv/bin/activate  # (Mac/Linux)

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Environment Variables

Create a .env file in the project root:

FLASK_APP=app.app
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-2.5-flash
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=500


(AI Advisor is optional — app works fully without it.)

5️⃣ Run the App

From project root:

flask run


Or directly:

cd app
python app.py


Then open:

http://127.0.0.1:5000

🧩 Example Workflow

Select a region from the dropdown (e.g., Busia).

Click Predict Risk → Flask backend generates 1–3 month forecasts.

Map colors update automatically (green/yellow/red by risk).

Sidebar displays detailed regional forecast metrics.

(Optional) AI Advisor generates a neutral, data-driven summary under “AI Brief.”

⚙️ Configuration Notes
Setting	Description
FLASK_APP	Entry module for flask run
GEMINI_API_KEY	Enables AI Advisor (optional)
LLM_TEMPERATURE	Controls creativity of AI outputs
LLM_MAX_TOKENS	Caps response length
app/utils/ai_cache.py	Prevents redundant Gemini calls (24h TTL)
🚀 Hosting on Vultr (summary)

Clone repo on server

Install Python 3.11 + dependencies

Add .env

Run with Gunicorn:

gunicorn app.app:app -b 0.0.0.0:5000


Reverse-proxy with Nginx → domain (e.g., droughtguard.tech)

🌐 Future Work

🔗 Automated Data Pipeline — Connect real-time NDVI, SPI, and price APIs.

🤖 Model Retraining Loop — Continuous learning from updated datasets.

📡 Country Expansion — East Africa, Horn of Africa regions.

💬 Alert System — Email/SMS triggers for threshold exceedance.

🧩 Explainability Dashboard — Add SHAP and feature attribution charts.

⚙️ Offline Mode — Deployable lightweight Flask container for field use.

⚖️ Ethical & Safety Considerations

Human-in-the-loop — All predictions are for analytical support, not direct operational decisions.

AI Transparency — Disclaimers shown for all Gemini outputs.

No Sensitive Instructions — Prompts are phrased for neutral analytical summaries only.

Privacy & Fairness — Regional data only, no individual identifiers.

👥 Contributors

Team SentinelSight

Role	Member
🧠 Data & Modeling	Oth
⚙️ Backend & AI Integration	Sid
🎨 Frontend & Deployment	Darsh
🏆 Hackathon Criteria
Category	Highlights
Impact	Tackles early detection of food insecurity in vulnerable communities
Innovation	Combines classical ML forecasting + generative AI explanations
Scalability	Modular, cloud-deployable architecture
Execution	End-to-end prototype with interactive visualization
Humanitarian Value	Supports evidence-based early interventions
📜 License

This project is licensed under the MIT License.
See the LICENSE file for full details.

📞 Contact

For collaborations or questions:
📧 team.sentinelsight@gmail.com

Built with ❤️ by Team SentinelSight — 24-hour prototype for social good
“Predict Early. Act Early. Save Lives.”

---

**Built with ❤️ by Team SentinelSight in 24 hours**
