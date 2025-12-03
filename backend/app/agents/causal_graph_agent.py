# backend/app/agents/causal_graph_agent.py

from typing import List, Dict, Any
import google.generativeai as genai

from ..core.config import settings

# Keep consistent with your other LLM agents
MODEL_NAME = "gemini-2.5-flash"


def _ensure_client_configured() -> None:
    """
    Ensure Gemini is configured before use.
    """
    if not settings.gemini_api_key:
        raise RuntimeError("Gemini API key not configured for causal graph.")
    genai.configure(api_key=settings.gemini_api_key)


def _build_deterministic_chain(
    refined_hypotheses: List[Dict[str, Any]],
    incident_summary: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Deterministically construct a simple causal chain based on hypothesis IDs and scores.
    This gives a stable structure that does not depend on LLM output.
    """
    by_id = {h.get("id"): h for h in refined_hypotheses}
    primary_id = incident_summary.get("primary_cause_id")
    primary = by_id.get(primary_id)

    if not primary:
        return {
            "root_cause": None,
            "root_cause_id": None,
            "cascade": [],
        }

    # Define a canonical ordering of causes/effects we expect
    # for typical incidents: dependency -> performance -> infra -> customer impact.
    chain_order: List[str] = []

    # Start from the primary; then add related hypotheses in a sensible order.
    # If dependency is present, treat it as earliest in the chain.
    if "H2" in by_id:
        chain_order.append("H2")

    # Performance degradation (latency / timeouts).
    if "H1" in by_id and "H1" not in chain_order:
        chain_order.append("H1")

    # Infrastructure saturation.
    if "H4" in by_id and "H4" not in chain_order:
        chain_order.append("H4")

    # Customer impact as final node.
    if "H5" in by_id and "H5" not in chain_order:
        chain_order.append("H5")

    # In case the primary is something else (e.g., H3), ensure it appears in the chain.
    if primary_id and primary_id not in chain_order:
        chain_order.insert(0, primary_id)

    # Build cascade with "node" and "caused_by" fields.
    cascade: List[Dict[str, Any]] = []
    for idx, hid in enumerate(chain_order):
        h = by_id[hid]
        caused_by = chain_order[idx - 1] if idx > 0 else None
        cascade.append(
            {
                "node": h.get("title"),
                "hypothesis_id": hid,
                "caused_by": caused_by,
                "score": h.get("score", 0.0),
            }
        )

    return {
        "root_cause": primary.get("title"),
        "root_cause_id": primary_id,
        "cascade": cascade,
    }


def _build_llm_summary(
    events: List[Dict[str, Any]],
    chain: Dict[str, Any],
) -> str:
    """
    Optional Gemini summary explaining the causal chain in natural language.
    This keeps structure deterministic but provides an executive explanation.
    """
    try:
        _ensure_client_configured()
    except Exception as e:
        # Fail gracefully and keep overall pipeline working.
        return f"Causal graph summary not available: {str(e)}"

    timeline_text = "\n".join(
        f"- {e.get('time')} | {e.get('message')}" for e in events
    )

    cascade_text = "\n".join(
        f"- {c['hypothesis_id']}: {c['node']} (caused_by={c['caused_by']})"
        for c in chain.get("cascade", [])
    )

    prompt = f"""
You are an SRE expert. A deterministic system has produced the following
incident timeline and causal chain.

Timeline:
{timeline_text}

Deterministic causal chain:
Root cause: {chain.get('root_cause')} (id={chain.get('root_cause_id')})
Cascade:
{cascade_text}

Write a concise, factual explanation of this causal chain:
- What the root cause is.
- How it propagated through the system.
- How it ultimately impacted customers.

Do not change the causal ordering. Do not invent new nodes.
Write in 2–4 short paragraphs.
"""

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        result = model.generate_content(prompt)
        return result.text or "Causal graph summary generation failed."
    except Exception as e:
        return f"Causal graph summary error: {str(e)}"


def build_causal_graph(
    events: List[Dict[str, Any]],
    refined_hypotheses: List[Dict[str, Any]],
    incident_summary: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Public entry point for Step 3.10.

    Returns a structure like:
    {
        "root_cause": "...",
        "root_cause_id": "H2",
        "cascade": [
            {"node": "...", "hypothesis_id": "H2", "caused_by": null, "score": 0.9},
            {"node": "...", "hypothesis_id": "H1", "caused_by": "H2", "score": 0.8},
            ...
        ],
        "llm_summary": "..."
    }
    """
    chain = _build_deterministic_chain(refined_hypotheses, incident_summary)
    llm_summary = _build_llm_summary(events, chain)

    chain["llm_summary"] = llm_summary
    return chain