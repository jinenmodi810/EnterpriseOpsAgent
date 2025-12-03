# backend/app/agents/explain_hypothesis_agent.py

from typing import List, Dict, Any


def explain_hypothesis(
    events: List[Dict[str, Any]],
    refined_hypotheses: List[Dict[str, Any]],
    hypothesis_id: str,
) -> Dict[str, Any]:
    """
    Produce a deterministic explanation for a selected hypothesis:
        - full explanation
        - supporting evidence (matching events)
        - conflicting evidence (events supporting rivals)
    """

    # 1) Identify selected hypothesis
    selected = next((h for h in refined_hypotheses if h["id"] == hypothesis_id), None)

    if not selected:
        return {
            "error": f"Hypothesis {hypothesis_id} not found."
        }

    # 2) Extract keywords from hypothesis title
    #    Helps us match supporting and conflicting events.
    title = selected["title"].lower()
    keywords = title.replace("/", " ").replace("-", " ").split()
    keywords = [k for k in keywords if len(k) > 3]

    supporting = []
    conflicting = []

    for e in events:
        msg = (e.get("message") or "").lower()

        # simple match heuristic for supporting evidence
        if any(k in msg for k in keywords):
            supporting.append(e)
            continue

        # conflicting evidence = events supporting other hypotheses
        # but not matching this one
        conflicting.append(e)

    return {
        "hypothesis_id": selected["id"],
        "title": selected["title"],
        "full_explanation": selected["explanation"],
        "supporting_evidence": supporting,
        "conflicting_evidence": conflicting,
    }