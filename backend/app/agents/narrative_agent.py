from typing import List, Dict, Any
import google.generativeai as genai

from ..core.config import settings


MODEL_NAME = "gemini-2.5-flash"


def _ensure_client_configured() -> None:
    if not settings.gemini_api_key:
        raise RuntimeError("Gemini API key not configured.")
    genai.configure(api_key=settings.gemini_api_key)


def generate_incident_narrative(
    events: List[Dict[str, Any]],
    refined_hypotheses: List[Dict[str, Any]],
    incident_summary: Dict[str, Any],
    similar_incidents: List[Dict[str, Any]],
) -> str:
    """
    Produce a structured natural-language narrative summarising the incident.
    This will be used by the frontend as the 'manager/executive-ready' storyline.
    """

    _ensure_client_configured()

    messages_text = "\n".join(
        f"- {e.get('time')} | {e.get('message')}" for e in events
    )

    hypotheses_text = "\n".join(
        f"- {h['id']}: {h['title']} (score={h['score']})"
        for h in refined_hypotheses
    )

    similar_text = "\n".join(
        f"- {i['id']}: {i['title']}"
        for i in similar_incidents
    )

    prompt = f"""
You are an SRE expert. Generate a precise, structured, executive-grade narrative
of the incident based on the following inputs.

Timeline:
{messages_text}

Refined Hypotheses:
{hypotheses_text}

Incident Summary:
Severity: {incident_summary.get('severity')}
Primary Cause: {incident_summary.get('primary_cause_title')}
Confidence: {incident_summary.get('confidence')}

Similar Incidents:
{similar_text}

Produce a clear, factual narrative of:
1. What happened.
2. Why it happened.
3. How it was mitigated.
4. What patterns match previous incidents.
5. What the organisation should focus on next.

Write in structured paragraphs, not bullet points.
Do not invent data.
"""

    try:
        result = genai.GenerativeModel(MODEL_NAME).generate_content(prompt)
        return result.text or "Narrative generation failed."
    except Exception as e:
        return f"Narrative generation error: {str(e)}"