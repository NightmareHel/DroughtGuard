# DroughtGuard AI Advisor - Setup and Runbook

## Prerequisites

1. **Python 3.11+**
2. **Virtual Environment** (recommended)
3. **Gemini API Key** from https://aistudio.google.com/

## Setup Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Flask and web dependencies
- LangChain and Gemini integration
- ML dependencies (XGBoost, scikit-learn)
- Caching utilities (cachetools)

### 2. Set Environment Variables

**Required:**
```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
```

**Optional (with defaults):**
```bash
export GEMINI_MODEL="gemini-1.5-pro-latest"      # Default
export LLM_TEMPERATURE="0.2"                      # Default
export LLM_TIMEOUT_SECS="20"                      # Default
export LANGCHAIN_CACHE_DB=".lc_cache.sqlite"     # Default
```

### 3. Run the Application

```bash
cd app
python app.py
```

The app will start on `http://localhost:5000`

## Testing the AI Advisor

### 1. Via Browser UI

1. Open `http://localhost:5000`
2. Select a region from the dropdown
3. Click "Predict Risk"
4. View the AI Advisor section with "Explain" and "Brief" buttons
5. Click buttons to get AI-generated explanations

### 2. Via API

**Get Explanation:**
```bash
curl "http://localhost:5000/api/explain/Nairobi?h=1"
```

**Get Brief:**
```bash
curl "http://localhost:5000/api/brief/Garissa?h=2"
```

**Force Fresh (bypass cache):**
```bash
curl "http://localhost:5000/api/explain/Baringo?h=3&force=true"
```

## Expected Output

### Explain Endpoint

```json
{
  "region": "Nairobi",
  "horizon": 1,
  "month": "2024-12",
  "cached": false,
  "data": {
    "explanation": "The forecast for Nairobi over the next month shows moderate drought risk based on recent NDVI anomalies and rainfall patterns.",
    "disclaimers": "These predictions are based on historical patterns and may not account for unexpected events."
  }
}
```

### Brief Endpoint

```json
{
  "region": "Garissa",
  "horizon": 1,
  "month": "2024-12",
  "cached": false,
  "data": {
    "explanation": "Detailed briefing text with 5-7 sentences...",
    "actions": [
      "Monitor local food prices for any sudden increases",
      "Ensure early warning systems are operational"
    ],
    "disclaimers": "Uncertainty note about predictions."
  }
}
```

## Features

### ✅ Dual Caching

1. **In-Memory TTL Cache** (24 hours)
   - Fast, thread-safe
   - Automatically expires

2. **LangChain SQLite Cache**
   - Persists across restarts
   - Reduces API calls

### ✅ Structured Output

- Pydantic schemas ensure consistent JSON
- Automatic parsing and validation

### ✅ Cost Control

- Caching reduces API calls
- Low temperature (0.2) for deterministic responses
- 20-second timeout prevents hanging requests

## Troubleshooting

### Error: "LLM not available"

**Cause:** `GEMINI_API_KEY` not set

**Fix:**
```bash
export GEMINI_API_KEY="your_key_here"
# Restart app
```

### Slow Responses

**Cause:** Cache not working

**Fix:**
1. Check response for `"cached": true`
2. Use `?force=true` to bypass cache
3. Clear SQLite cache: `rm .lc_cache.sqlite`

### "Module not found" errors

**Fix:**
```bash
pip install -r requirements.txt
```

### UI not showing AI Advisor

**Fix:**
1. Select a region and click "Predict Risk"
2. AI Advisor section appears after prediction
3. Click "Explain" or "Brief" buttons

## File Structure

```
app/
├── utils/
│   ├── llm_chain.py      # LangChain + Gemini integration
│   └── ai_cache.py        # TTL cache implementation
├── app.py                 # Flask endpoints
├── static/
│   └── script.js          # AI Advisor UI integration
└── templates/
    └── index.html         # AI Advisor UI components

docs/
└── AI_ADVISOR_LANGCHAIN.md   # Detailed documentation
```

## Next Steps

1. ✅ Set `GEMINI_API_KEY`
2. ✅ Start Flask app
3. ✅ Test `/api/explain/<region>?h=1`
4. ✅ Use UI to view AI explanations
5. ✅ Monitor cache hits in logs

## Integration Notes

- AI Advisor provides **post-hoc explanations** (not used for training)
- Explains the model's predictions using available features
- Caches responses to minimize costs
- Returns JSON for both API and UI consumption
