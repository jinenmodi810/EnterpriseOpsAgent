# backend/app/schemas/analysis.py

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TimelineEvent(BaseModel):
    time: Optional[str] = Field(None, description="ISO timestamp of the event")
    message: str = Field(..., description="Human-readable message")
    event_type: Optional[str] = Field(None, description="Type of the event (alert, error, infra, etc.)")
    phase: Optional[str] = Field(None, description="Lifecycle phase (detection, mitigation, resolution)")
    source: Optional[str] = Field(None, description="Source system (alert, log, infra, customer)")
    level: Optional[str] = Field(None, description="Severity level (info, warning, critical, etc.)")


class Hypothesis(BaseModel):
    id: str
    title: str
    score: float
    explanation: str


class RuleBasedHypothesis(BaseModel):
    id: str
    title: str
    score: float
    explanation: str


class SimilarIncident(BaseModel):
    id: str
    title: str
    summary: str
    similarity: float


class IncidentSummary(BaseModel):
    severity: str
    primary_cause_id: Optional[str]
    primary_cause_title: Optional[str]
    primary_cause_category: Optional[str]
    confidence: float


class RecommendedAction(BaseModel):
    id: str
    title: str
    description: str
    owner: str
    priority: str


class TimelineCounts(BaseModel):
    total: int
    detection: int
    mitigation: int
    resolution: int


class TimelineStory(BaseModel):
    detection: str
    mitigation: str
    resolution: str
    counts: TimelineCounts


class AnalyzeResponse(BaseModel):
    timeline_preview: List[TimelineEvent]

    root_cause_hypotheses: List[Hypothesis]
    llm_commentary: Optional[str]
    llm_model: Optional[str]

    rule_based_hypotheses: List[RuleBasedHypothesis]
    similar_incidents: List[SimilarIncident]

    incident_summary: IncidentSummary
    recommended_actions: List[RecommendedAction]

    timeline_story: TimelineStory

    incident_narrative: Optional[str] = Field(
        None,
        description="Executive-ready narrative produced by Gemini; may be null if generation fails."
    )

    # For flexibility, in case you later want to add extra fields without breaking clients
    extra_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional bag for future non-breaking extensions."
    )