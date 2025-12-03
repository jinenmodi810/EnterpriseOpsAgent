from typing import List, Dict, Any, Tuple
import json
import re

import google.generativeai as genai
from ..core.config import settings

# Use an available model
GEMINI_MODEL_NAME = "models/gemini-2.5-flash"


def _get_model():
    if not settings.gemini_api_key:
        raise RuntimeError("Gemini API key not configured.")

    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(GEMINI_MODEL_NAME)


def _extract_json(text: str) -> dict:
    """
    Extract the first valid JSON object from the model output.
    Handles cases where model adds Markdown or extra text.
    """
    json_pattern = r"\{[\s\S]*\}"
    match = re.search(json_pattern, text)
    if not match:
        raise ValueError("No JSON object found in LLM output.")
    return json.loads(match.group(0))


def refine_root_cause_with_gemini(
    events: List[Dict[str, Any]],
    rule_based_hypotheses: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], str]:

    if not rule_based_hypotheses:
        return rule_based_hypotheses, "No hypotheses provided."

    try:
        model = _get_model()
    except Exception as e:
        return rule_based_hypotheses, f"Gemini not configured: {e}"

    sample_messages = [e.get("message", "") for e in events[:30]]
    incident_text = "\n".join(f"- {msg}" for msg in sample_messages if msg)

    hypotheses_json = json.dumps(rule_based_hypotheses, indent=2)

    prompt = f"""
You are an expert SRE incident analyst.

Refine the hypotheses and explain your reasoning.

Incident messages:
{incident_text}

Rule-based hypotheses:
{hypotheses_json}

Return EXACTLY this JSON structure, with no text before or after:

{{
  "refined": [...],
  "commentary": "..."
}}
"""

    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()

        data = _extract_json(raw_text)

        refined = data.get("refined", rule_based_hypotheses)
        commentary = data.get("commentary", "")

        if not isinstance(refined, list):
            return rule_based_hypotheses, "Invalid refined format."

        return refined, commentary

    except Exception as e:
        return rule_based_hypotheses, f"Gemini exception occurred: {e}"