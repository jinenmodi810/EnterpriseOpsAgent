# backend/app/agents/contrastive_agent.py

from typing import List, Dict, Any
import google.generativeai as genai

from ..core.config import settings

MODEL_NAME = "gemini-2.5-flash"


def _ensure_client_configured() -> None:
    """
    Ensure Gemini client is configured with an API key.
    """
    if not settings.gemini_api_key:
        raise RuntimeError("Gemini API key not configured.")
    genai.configure(api_key=settings.gemini_api_key)


def generate_contrastive_explanations(
    events: List[Dict[str, Any]],
    refined_hypotheses: List[Dict[str, Any]],
    incident_summary: Dict[str, Any],
) -> str:
    """
    Generate contrastive explanations:

      - Why the primary (winning) hypothesis is correct.
      - Why alternative hypotheses are weaker.
      - What evidence supports vs contradicts each.

    Output is a natural-language explanation string that the frontend
    can render in a dedicated panel.
    """

    if not refined_hypotheses:
        return "No hypotheses available for contrastive explanation."

    _ensure_client_configured()

    # Determine primary hypothesis from incident_summary if possible.
    primary_id = incident_summary.get("primary_cause_id")
    primary = None
    for h in refined_hypotheses:
        if h.get("id") == primary_id:
            primary = h
            break

    # Fallback: take the highest-scoring hypothesis.
    if primary is None:
        primary = max(refined_hypotheses, key=lambda h: h.get("score", 0.0))
        primary_id = primary.get("id")

    primary_title = primary.get("title", "")
    primary_score = primary.get("score", 0.0)

    # Choose a few competing hypotheses (up to 3 others).
    competitors: List[Dict[str, Any]] = [
        h for h in refined_hypotheses if h.get("id") != primary_id
    ][:3]

    timeline_text = "\n".join(
        f"- {e.get('time')} | {e.get('message')}"
        for e in events
    )

    hypotheses_text = "\n".join(
        f"- {h.get('id')}: {h.get('title')} (score={h.get('score')})"
        for h in refined_hypotheses
    )

    competitors_text = "\n".join(
        f"- {c.get('id')}: {c.get('title')} (score={c.get('score')})"
        for c in competitors
    ) or "None (no competitors)."

    prompt = f"""
You are an SRE and reliability engineering expert.

You are given:
1) A timeline of incident events.
2) A set of refined root-cause hypotheses with scores in [0,1].
3) A primary winning hypothesis chosen by the system.

Your task: produce a clear, contrastive explanation that answers:
- Why the primary hypothesis is the best explanation.
- Why the alternative hypotheses are weaker or less supported.
- What concrete evidence from the timeline supports or contradicts each.

Important constraints:
- Be factual and only use information present in the timeline and hypotheses.
- Do not invent events or evidence.
- Write for an SRE lead or engineering manager who wants a crisp justification.
- Use short paragraphs, not bullets, but you may refer to hypothesis IDs (H1, H2, etc.).

Timeline:
{timeline_text}

Refined Hypotheses:
{hypotheses_text}

Primary (Winning) Hypothesis:
- ID: {primary_id}
- Title: {primary_title}
- Score: {primary_score}

Competing Hypotheses:
{competitors_text}

Now write a structured explanation with the following sections:

1) Primary hypothesis justification.
2) Why each alternative is weaker.
3) Evidence supporting the primary hypothesis.
4) Any evidence that contradicts or fails to support alternatives.

Keep the explanation concise but precise.
"""

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        result = model.generate_content(prompt)
        text = getattr(result, "text", None)
        if not text:
            return "Contrastive explanation generation failed."
        return text
    except Exception as exc:
        return f"Contrastive explanation error: {str(exc)}"