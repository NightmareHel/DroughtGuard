"""
llm_chain.py
Minimal Gemini integration used by app.app:
- setup_cache(): configure Gemini client (no-op cache placeholder)
- gemini_ready(): report readiness and specific reason if not
- get_explanation(...) / get_brief(...): build compact prompts and return JSON dicts
This file intentionally avoids LangChain to keep imports simple.
"""

from __future__ import annotations
import os
import json
from typing import Dict, Any

# --- Load env early if python-dotenv is present (safe no-op if not installed)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# --- Try to import Gemini SDK
try:
    import google.generativeai as genai
    _GEMINI_IMPORTED = True
except Exception:
    genai = None  # type: ignore
    _GEMINI_IMPORTED = False

# --- Config from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "500"))

# --------------------------------------------------------------------------------------
# Public API required by app.app
#   - setup_cache()
#   - gemini_ready() -> (bool, reason_str)
#   - get_explanation(facts, region, horizon, month_str) -> dict
#   - get_brief(facts, region, horizon, month_str) -> dict
# --------------------------------------------------------------------------------------

def setup_cache() -> None:
    """Configure Gemini client once. (No local cache; name kept for compatibility.)"""
    if _GEMINI_IMPORTED and GEMINI_API_KEY:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            print(f"[OK] Gemini configured (model={GEMINI_MODEL})")
        except Exception as e:
            print(f"[WARN] Gemini configure failed: {e}")


def gemini_ready() -> tuple[bool, str]:
    """Return (is_ready, reason). Use this in /api/ai/health and before calls."""
    if not _GEMINI_IMPORTED:
        return (False, "google-generativeai package not installed")
    if not GEMINI_API_KEY:
        return (False, "GEMINI_API_KEY missing")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        _ = genai.GenerativeModel(GEMINI_MODEL)  # validate model name
        return (True, "ok")
    except Exception as e:
        return (False, f"Gemini init failed: {e}")


# --------------------------------------------------------------------------------------
# Internal helpers
# --------------------------------------------------------------------------------------

def _num(x):
    try:
        return float(x)
    except Exception:
        return None

def _fmt(x):
    try:
        return f"{float(x):.2f}"
    except Exception:
        return None

def _format_signals(facts: Dict[str, Any]) -> str:
    """Compact bullets with only available fields; ensures prompt varies by region."""
    parts = []
    v = _fmt(facts.get("ndvi_anomaly"));      parts.append(f"- NDVI Anomaly: {v}") if v is not None else None
    v = _fmt(facts.get("spi1"))
    if v is not None:
        parts.append(f"- SPI-1: {v}")
    else:
        v = _fmt(facts.get("spi3"))
        parts.append(f"- SPI-3: {v}") if v is not None else None
    v = _fmt(facts.get("price_yoy"));         parts.append(f"- Food Price YoY: {v}") if v is not None else None
    v = _fmt(facts.get("delta_ndvi"));        parts.append(f"- NDVI Trend: {v}") if v is not None else None
    v = _fmt(facts.get("delta_price"));       parts.append(f"- Price Trend: {v}") if v is not None else None
    return "\n".join(parts) if parts else "- Using available environmental and market indicators"

def _make_prompt(mode: str, region: str, horizon_label: str, current_month: str,
                 prob: float, risk_tier: str, signals_text: str) -> str:
    """Build strict-JSON prompt. We log a hash so you can prove it varies by region/h."""
    if mode == "explain":
        system = (
            "Context: [structured facts: NDVI, rainfall anomaly, price inflation, probability].
            "Task: Produce a one-paragraph non-operational risk summary and a short list (3) of monitoring questions for humanitarian analysts." 
            "Do NOT provide operational instructions, procurement steps, or contact details for distribution."
            "Output format: JSON { "summary": "...", "monitoring_questions": ["...","...","..."] }"

        )
        user = f"""Explain the risk for {region}, {horizon_label} ahead (as of {current_month}).

Context:
- Risk Probability: {prob:.2f}
- Risk Tier: {risk_tier}

Environmental Signals:
{signals_text}

Respond with JSON only:
{{
  "explanation": "3-5 sentence explanation",
  "disclaimers": "One sentence uncertainty note"
}}"""
    else:
        system = (
                "You are an environmental analysis assistant. "
                "Interpret climate and agricultural indicators in a neutral and factual tone. "
                "Do not discuss humanitarian crises or suffering. "
                "Summarize patterns in vegetation, rainfall, and market indicators."
            )
    user = f"""Brief the risk for {region}, {horizon_label} ahead (as of {current_month}).

Context:
- Risk Probability: {prob:.2f}
- Risk Tier: {risk_tier}

Environmental Signals:
{signals_text}

Respond with JSON only:
{{
  "explanation": "5-7 sentence detailed briefing",
  "actions": ["Action 1", "Action 2"],
  "disclaimers": "One sentence uncertainty note"    
}}"""
    prompt = f"{system}\n\n{user}"
    try:
        print(f"[DEBUG] PROMPT HASH region={region} horizon={horizon_label}: {hash(prompt)}")
    except Exception:
        pass
    return prompt

def _call_gemini_json(prompt: str) -> Dict[str, Any]:
    ok, reason = gemini_ready()
    if not ok:
        raise RuntimeError(reason)

    model = genai.GenerativeModel(GEMINI_MODEL)

    try:
        resp = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=LLM_TEMPERATURE,
                max_output_tokens=LLM_MAX_TOKENS,
            ),
        )

        # --- Safely extract text (without touching resp.text) ---
        text = ""
        try:
            if hasattr(resp, "candidates") and resp.candidates:
                parts = []
                for c in resp.candidates:
                    if hasattr(c, "content") and hasattr(c.content, "parts"):
                        for p in c.content.parts:
                            if hasattr(p, "text"):
                                parts.append(p.text)
                text = "".join(parts).strip()
        except Exception as e:
            print(f"[WARN] Could not parse response parts: {e}")

        # --- Handle blocked or empty output ---
        if not text:
            print("[WARN] Gemini produced no usable text — likely safety-blocked.")
            try:
                if hasattr(resp, "candidates") and resp.candidates:
                    print(json.dumps(resp.candidates[0].safety_ratings, indent=2))
            except Exception:
                print("[WARN] Could not dump safety_ratings.")
            return {
                "explanation": "AI response was withheld by safety filters or returned empty.",
                "disclaimers": "Gemini output unavailable. Proceed with model predictions only."
            }

        print("[DEBUG] Gemini raw response text:", text[:300])

        # --- Extract JSON from text ---
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError(f"No JSON found in response: {text[:200]}")

        data = json.loads(text[start:end + 1])
        if "explanation" not in data:
            raise ValueError(f"JSON missing 'explanation': {data}")
        return data

    except Exception as e:
        print(f"[ERROR] Gemini call failed: {e}")
        import traceback; traceback.print_exc()
        # Safe fallback so frontend never breaks
        return {
            "explanation": f"Gemini error: {e}",
            "disclaimers": "Fallback text used due to LLM error."
        }


# --------------------------------------------------------------------------------------
# Public functions used by app.app
# --------------------------------------------------------------------------------------

def get_explanation(facts: Dict[str, Any], region: str, horizon: int, month_str: str) -> Dict[str, Any]:
    label = f"+{horizon}m" if horizon > 0 else "current"
    prob = _num(facts.get("prob")) or 0.0
    tier = str(facts.get("risk_tier", "Unknown"))
    prompt = _make_prompt("explain", region, label, month_str, prob, tier, _format_signals(facts))
    return _call_gemini_json(prompt)

def get_brief(facts: Dict[str, Any], region: str, horizon: int, month_str: str) -> Dict[str, Any]:
    label = f"+{horizon}m" if horizon > 0 else "current"
    prob = _num(facts.get("prob")) or 0.0
    tier = str(facts.get("risk_tier", "Unknown"))
    prompt = _make_prompt("brief", region, label, month_str, prob, tier, _format_signals(facts))
    return _call_gemini_json(prompt)
