# backend/app/routes/explain_hypothesis.py

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Body

from ..agents.explain_hypothesis_agent import explain_hypothesis
from ..agents.root_cause_agent import generate_root_cause_analysis

router = APIRouter()

@router.post("/", summary="Explain a selected hypothesis", tags=["explain"])
async def explain_selected_hypothesis(
    payload: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """
    Input:
        {
            "events": [...],
            "hypothesis_id": "H1"
        }

    Output:
        {
            "hypothesis_id": "...",
            "title": "...",
            "full_explanation": "...",
            "supporting_evidence": [...],
            "conflicting_evidence": [...]
        }
    """

    events = payload.get("events")
    hypothesis_id = payload.get("hypothesis_id")

    if not events or not hypothesis_id:
        raise HTTPException(
            status_code=400,
            detail="Both 'events' and 'hypothesis_id' are required."
        )

    # RCA refinement to know full hypothesis metadata
    analysis = generate_root_cause_analysis(events, use_gemini=True)
    refined = analysis["hypotheses"]

    return explain_hypothesis(events, refined, hypothesis_id)