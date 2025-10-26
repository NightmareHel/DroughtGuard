# AI Advisor Integration - LangChain + Gemini

## Overview

The DroughtGuard AI Advisor uses **LangChain** with **Google's Gemini** to provide natural language explanations for drought risk forecasts. This integration provides post-hoc explanations, not used for training the models.

## Architecture

### Components

1. **LangChain** - Orchestrates prompts, parsing, and caching
2. **Gemini 1.5 Pro** - Google's multimodal LLM via `langchain-google-genai`
3. **Structured Output** - Pydantic schemas ensure consistent JSON responses
4. **Dual Caching** - SQLite cache + in-memory TTL cache for cost/latency control

### Flow

```
User selects region
  → Flask endpoint receives request
  → Check TTL cache (24h default)
  → Check LangChain SQLite cache
  → Build prompt with risk facts
  → Call Gemini API
  → Parse JSON response
  → Cache and return
```

## Environment Variables

Required:
- `GEMINI_API_KEY` - Get from https://aistudio.google.com/

Optional:
- `GEMINI_MODEL` - Default: `gemini-1.5-pro-latest`
- `LLM_TEMPERATURE` - Default: `0.2` (lower = more deterministic)
- `LLM_TIMEOUT_SECS` - Default: `20`
- `LANGCHAIN_CACHE_DB` - Default: `.lc_cache.sqlite`

## Endpoints

### GET /api/explain/<region>?h=1|2|3

Returns concise 3-5 sentence operational explanation.

**Response:**
```json
{
  "region": "Garissa",
  "horizon": 1,
  "month": "2024-12",
  "cached": false,
  "data": {
    "explanation": "The forecast indicates...",
    "disclaimers": "Predictions are based on historical patterns..."
  }
}
```

### GET /api/brief/<region>?h=1|2|3

Returns detailed 5-7 sentence briefing with actionable recommendations.

**Response:**
```json
{
  "region": "Garissa",
  "horizon": 1,
  "month": "2024-12",
  "cached": false,
  "data": {
    "explanation": "Detailed analysis...",
    "actions": ["Action 1", "Action 2"],
    "disclaimers": "Uncertainty note..."
  }
}
```

### Query Parameters

- `h` - Horizon (1, 2, or 3 months ahead) - Required
- `force=true` - Bypass cache and force fresh response

## Caching Strategy

### Layer 1: In-Memory TTL Cache (`cachetools`)
- Key: `(region, month, horizon, mode)`
- TTL: 24 hours
- Thread-safe: Yes

### Layer 2: LangChain SQLite Cache
- Key: Prompt content hash
- Persists across restarts
- Location: `.lc_cache.sqlite`

### Cache Behavior

1. Check in-memory cache first
2. If miss, check SQLite cache (Gemini API call may be cached)
3. If both miss, call Gemini API
4. Store in both caches

To force refresh: Add `?force=true` to URL

## Example Usage

### cURL

```bash
# Get explanation for Garissa, 1 month ahead
curl "http://localhost:5000/api/explain/Garissa?h=1"

# Get brief for Nairobi, force fresh
curl "http://localhost:5000/api/brief/Nairobi?h=2&force=true"
```

### Python

```python
import requests

# Get explain
response = requests.get("http://localhost:5000/api/explain/Garissa?h=1")
data = response.json()
print(data['data']['explanation'])

# Get brief
response = requests.get("http://localhost:5000/api/brief/Nairobi?h=3")
data = response.json()
print(f"Explanation: {data['data']['explanation']}")
print(f"Actions: {data['data']['actions']}")
```

## Prompts

### Explain Mode

**System:** "You are a humanitarian early-warning analyst..."

**User Template:**
```
Explain the drought risk forecast for {region}, {horizon} months ahead ({current_month}).

Context:
- Risk Probability: {prob:.2f}
- Risk Tier: {risk_tier}

Environmental Signals:
{signals}
```

**Output Schema:**
```json
{
  "explanation": "string",
  "disclaimers": "string"
}
```

### Brief Mode

Similar to explain but:
- More detailed (5-7 sentences)
- Includes 1-2 actionable recommendations
- Returns `actions` array in schema

## Cost Management

1. **Caching** - Responses cached for 24 hours
2. **Concise Prompts** - Limited token count
3. **Timeout** - 20 second default timeout
4. **Temperature** - Low (0.2) for deterministic responses

## Error Handling

If `GEMINI_API_KEY` is not set:
```json
{
  "error": "LLM not available",
  "detail": "GEMINI_API_KEY not configured"
}
```

HTTP 503 indicates LLM is unavailable (check API key).

## Monitoring

Logs show:
- Cache hits/misses
- API latency
- Model errors

Example log output:
```
[OK] Initialized Gemini LLM: gemini-1.5-pro-latest
[OK] LangChain SQLite cache enabled: .lc_cache.sqlite
```

## Files

- `app/utils/llm_chain.py` - LangChain integration
- `app/utils/ai_cache.py` - TTL cache implementation
- `app/app.py` - Flask endpoints
- `app/static/script.js` - Frontend integration
- `app/templates/index.html` - UI components

## Testing

1. Start Flask app: `python app/app.py`
2. Select a region in the UI
3. Click "Explain" or "Brief" in AI Advisor section
4. View cached badge if response was cached

## Limitations

- Requires internet connection for Gemini API
- Subject to Gemini rate limits
- Caching assumes static forecasts (force refresh for updates)

## Troubleshooting

**Error: "LLM not available"**
- Check `GEMINI_API_KEY` is set
- Verify API key is valid at https://aistudio.google.com/

**Slow responses**
- Check cache is working (`cached: true` in response)
- Monitor API latency in logs
- Consider increasing `LLM_TIMEOUT_SECS`

**Stale responses**
- Use `?force=true` to bypass cache
- Clear SQLite cache: `rm .lc_cache.sqlite`

