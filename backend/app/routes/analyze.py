from typing import List, Dict, Any
import io
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from ..agents.ingestion_agent import build_timeline_from_dataframe
from ..agents.root_cause_agent import generate_root_cause_analysis

router = APIRouter()

# Store the most recent analysis in memory
LATEST_RESULT: Dict[str, Any] = {}


@router.post("/", summary="Analyze incident CSV", tags=["analyze"])
async def analyze_csv(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Analyze an incident CSV:
      1. Parse the CSV into a dataframe.
      2. Convert it into a structured timeline.
      3. Generate root-cause hypotheses (rule-based + Gemini + RAG + calibration).
    """
    try:
        raw_bytes = await file.read()
        df = pd.read_csv(io.BytesIO(raw_bytes))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read CSV file: {exc}")

    try:
        events: List[Dict[str, Any]] = build_timeline_from_dataframe(
            df, source_name=file.filename or "csv"
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    analysis = generate_root_cause_analysis(events, use_gemini=True)

    timeline_preview: List[Dict[str, Any]] = events[:20]

    result = {
        "timeline_preview": timeline_preview,
        "root_cause_hypotheses": analysis["hypotheses"],
        "llm_commentary": analysis.get("llm_commentary"),
        "llm_model": analysis.get("llm_model"),
        "rule_based_hypotheses": analysis.get("rule_based"),
        "similar_incidents": analysis.get("similar_incidents"),
        "incident_summary": analysis.get("incident_summary"),
        "recommended_actions": analysis.get("recommended_actions"),
        "timeline_story": analysis.get("timeline_story"),
        "incident_narrative": analysis.get("incident_narrative"),
        "calibrated_scores": analysis.get("calibrated_scores"),
        "calibrated_confidence": analysis.get("calibrated_confidence"),
        "evidence_strength_report": analysis.get("evidence_strength_report"),
        "contrastive_explanations": analysis.get("contrastive_explanations"),
        "causal_graph": analysis.get("causal_graph"),
    }

    # Save for later retrieval
    global LATEST_RESULT
    LATEST_RESULT = result
    return result


@router.get("/", summary="Get last analyzed result", tags=["analyze"])
async def get_last_analysis() -> Dict[str, Any]:
    """
    Return the most recent analysis result, if available.
    """
    if not LATEST_RESULT:
        return JSONResponse({"message": "No previous analysis found."}, status_code=404)
    return LATEST_RESULT