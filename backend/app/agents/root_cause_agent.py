# backend/app/agents/root_cause_agent.py

from typing import List, Dict, Any

from .gemini_agent import refine_root_cause_with_gemini
from .similar_incident_agent import find_similar_incidents
from .narrative_agent import generate_incident_narrative
from .calibration_agent import calibrate_hypotheses
from .contrastive_agent import generate_contrastive_explanations
from .causal_graph_agent import build_causal_graph


def _score_keyword_signals(events: List[Dict[str, Any]], keywords: List[str]) -> float:
    """
    Simple signal: how many event messages mention any of the given keywords,
    normalised to [0, 1].
    """
    if not events:
        return 0.0

    hits = 0
    for e in events:
        msg = (e.get("message") or "").lower()
        if any(kw in msg for kw in keywords):
            hits += 1

    return hits / len(events)


def generate_rule_based_hypotheses(
    events: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Baseline rule-based hypotheses using simple keyword and level heuristics.
    This is Step 3.2: deterministic, no LLMs, stable.
    """

    timeout_score = _score_keyword_signals(
        events,
        ["timeout", "latency", "slow", "connection timed out", "exceeded threshold"],
    )
    dependency_score = _score_keyword_signals(
        events,
        ["payment", "payments-service", "database", "db", "redis", "kafka", "third-party"],
    )
    deploy_score = _score_keyword_signals(
        events,
        ["deploy", "deployment", "release", "rollback", "version"],
    )
    infra_score = _score_keyword_signals(
        events,
        ["cpu", "memory", "disk", "node", "pod", "kubernetes", "k8s", "autoscale"],
    )
    customer_impact_score = _score_keyword_signals(
        events,
        ["customer", "user", "client", "unable to", "cannot checkout", "500 error"],
    )

    hypotheses: List[Dict[str, Any]] = []

    hypotheses.append(
        {
            "id": "H1",
            "title": "Latency or timeout in critical path service",
            "score": round(timeout_score, 2),
            "explanation": (
                "Multiple messages reference latency, timeouts, or slow responses. "
                "This suggests a performance-related degradation in a key service."
            ),
        }
    )

    hypotheses.append(
        {
            "id": "H2",
            "title": "Downstream dependency or external service failure",
            "score": round(dependency_score, 2),
            "explanation": (
                "Logs refer to databases, payment systems, or other dependencies. "
                "This suggests the root cause may be in a downstream or third-party service."
            ),
        }
    )

    hypotheses.append(
        {
            "id": "H3",
            "title": "Recent deployment or configuration change regression",
            "score": round(deploy_score, 2),
            "explanation": (
                "Mentions of deployment, release, or rollback indicate that a recent "
                "change may have introduced the incident."
            ),
        }
    )

    hypotheses.append(
        {
            "id": "H4",
            "title": "Infrastructure saturation or capacity issue",
            "score": round(infra_score, 2),
            "explanation": (
                "Messages referencing CPU, memory, pods, or autoscaling suggest an "
                "infrastructure resource bottleneck."
            ),
        }
    )

    hypotheses.append(
        {
            "id": "H5",
            "title": "High customer impact and degraded user experience",
            "score": round(customer_impact_score, 2),
            "explanation": (
                "Customer or user complaints indicate direct impact. This is not a pure "
                "internal warning, but a user-facing outage or severe degradation."
            ),
        }
    )

    hypotheses.sort(key=lambda h: h["score"], reverse=True)
    return hypotheses


def _infer_incident_summary(
    refined_hypotheses: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Derive a compact incident summary (severity, primary cause, confidence)
    from the refined hypotheses.
    """
    if not refined_hypotheses:
        return {
            "severity": "unknown",
            "primary_cause_id": None,
            "primary_cause_title": None,
            "primary_cause_category": None,
            "confidence": 0.0,
        }

    primary = max(refined_hypotheses, key=lambda h: h.get("score", 0.0))
    primary_id = primary.get("id")
    primary_title = primary.get("title")
    confidence = float(primary.get("score", 0.0))

    cause_category_map = {
        "H1": "performance",
        "H2": "dependency",
        "H3": "deployment",
        "H4": "infra",
        "H5": "customer-impact",
    }
    category = cause_category_map.get(primary_id, "unknown")

    max_score = max(h.get("score", 0.0) for h in refined_hypotheses)
    if max_score >= 0.8:
        severity = "critical"
    elif max_score >= 0.5:
        severity = "high"
    elif max_score > 0:
        severity = "medium"
    else:
        severity = "low"

    return {
        "severity": severity,
        "primary_cause_id": primary_id,
        "primary_cause_title": primary_title,
        "primary_cause_category": category,
        "confidence": round(confidence, 2),
    }


def _build_recommended_actions(
    incident_summary: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Derive recommended follow-up actions from the incident summary.
    Deterministic, judge-friendly.
    """
    actions: List[Dict[str, Any]] = []

    category = incident_summary.get("primary_cause_category")

    if category == "dependency":
        actions.append(
            {
                "id": "A1",
                "title": "Stabilise downstream dependency",
                "description": (
                    "Coordinate with the owners of the failing downstream service to stabilise it "
                    "(restart if needed, rollback risky changes, validate health checks and SLIs)."
                ),
                "owner": "dependency_owner",
                "priority": "p0",
            }
        )
    elif category == "infra":
        actions.append(
            {
                "id": "A2",
                "title": "Right-size and harden infrastructure capacity",
                "description": (
                    "Review autoscaling configuration, resource requests/limits, and pod distribution "
                    "to prevent CPU or memory saturation during traffic spikes."
                ),
                "owner": "infra_team",
                "priority": "p0",
            }
        )
    elif category == "deployment":
        actions.append(
            {
                "id": "A3",
                "title": "Audit recent changes and improve rollout safety",
                "description": (
                    "Review recent deployments and configuration changes; consider canary rollouts, "
                    "automatic rollback rules, and stronger pre-deployment checks."
                ),
                "owner": "platform_team",
                "priority": "p0",
            }
        )
    elif category == "performance":
        actions.append(
            {
                "id": "A4",
                "title": "Optimise critical path performance",
                "description": (
                    "Profile the critical request path, tune timeouts and retries, and ensure that "
                    "performance regressions are caught via SLOs and alerting."
                ),
                "owner": "service_owner",
                "priority": "p1",
            }
        )

    actions.append(
        {
            "id": "A5",
            "title": "Post-incident review",
            "description": (
                "Schedule a blameless post-incident review covering detection quality, mitigation steps, "
                "communication, and long-term prevention."
            ),
            "owner": "sre_lead",
            "priority": "p2",
        }
    )
    actions.append(
        {
            "id": "A6",
            "title": "Review similar incidents and update playbooks",
            "description": (
                "Review historical incidents similar to this one and refine or update their runbooks "
                "and auto-mitigation strategies."
            ),
            "owner": "sre_team",
            "priority": "p2",
        }
    )

    return actions


def _build_timeline_story(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Step 3.7 (Option C):
    Produce a deterministic 'before / during / after' narrative from the timeline.
    No extra LLM calls, purely structured from events.
    """
    if not events:
        return {
            "detection": "",
            "mitigation": "",
            "resolution": "",
            "counts": {
                "total": 0,
                "detection": 0,
                "mitigation": 0,
                "resolution": 0,
            },
        }

    detection_events = [e for e in events if e.get("phase") == "detection"]
    mitigation_events = [e for e in events if e.get("phase") == "mitigation"]
    resolution_events = [e for e in events if e.get("phase") == "resolution"]

    def _summarise_phase(phase_events: List[Dict[str, Any]], phase_name: str) -> str:
        if not phase_events:
            return f"No explicit {phase_name} events recorded."

        first = phase_events[0]
        last = phase_events[-1]
        first_msg = first.get("message", "")
        last_msg = last.get("message", "")
        first_time = first.get("time", "")
        last_time = last.get("time", "")

        if first is last:
            return (
                f"{phase_name.capitalize()} phase: started at {first_time} "
                f"with '{first_msg}'."
            )
        return (
            f"{phase_name.capitalize()} phase: from {first_time} to {last_time}. "
            f"Started with '{first_msg}' and ended with '{last_msg}'."
        )

    detection_summary = _summarise_phase(detection_events, "detection")
    mitigation_summary = _summarise_phase(mitigation_events, "mitigation")
    resolution_summary = _summarise_phase(resolution_events, "resolution")

    return {
        "detection": detection_summary,
        "mitigation": mitigation_summary,
        "resolution": resolution_summary,
        "counts": {
            "total": len(events),
            "detection": len(detection_events),
            "mitigation": len(mitigation_events),
            "resolution": len(resolution_events),
        },
    }


def generate_root_cause_analysis(
    events: List[Dict[str, Any]],
    use_gemini: bool = True,
) -> Dict[str, Any]:
    """
    Main orchestrator:
      - 3.2: rule-based hypotheses
      - 3.4: Gemini refinement + commentary
      - 3.6: RAG (similar incidents) + incident summary + recommended actions
      - 3.7: Timeline story
      - 3.8: Calibration layer (scores, confidence, evidence report)
    """

    # 1) Rule-based hypotheses
    rule_based = generate_rule_based_hypotheses(events)

    # 2) Optional Gemini refinement
    if use_gemini:
        refined, commentary = refine_root_cause_with_gemini(events, rule_based)
    else:
        refined = rule_based
        commentary = "Gemini refinement disabled."

    # 3) RAG: similar historical incidents from KB
    similar_incidents = find_similar_incidents(events, top_k=3)

    # 4) Derived summary from refined scores
    incident_summary = _infer_incident_summary(refined)

        # 4) Derived summary and recommended actions
    incident_summary = _infer_incident_summary(refined)
    recommended_actions = _build_recommended_actions(incident_summary)

    # 4b) Contrastive explanations: why primary vs alternatives (Step 3.9)
    contrastive_explanations = generate_contrastive_explanations(
        events,
        refined,
        incident_summary,
    )

    # 5) Timeline narrative (3.7)
    timeline_story = _build_timeline_story(events)

    # 5) Calibration layer (3.8)
    calibrated_hypotheses, calibrated_confidence, evidence_strength_report = calibrate_hypotheses(
        refined, events
    )
    incident_summary["confidence"] = round(calibrated_confidence, 2)

    # 6) Recommended actions based on calibrated summary
    recommended_actions = _build_recommended_actions(incident_summary)

    # 7) Manager / executive narrative using calibrated hypotheses
    incident_narrative = generate_incident_narrative(
        events,
        calibrated_hypotheses,
        incident_summary,
        similar_incidents,
    )
     # 7) Causal graph (Step 3.10)
    causal_graph = build_causal_graph(
        events=events,
        refined_hypotheses=refined,
        incident_summary=incident_summary,
    )

    # 8) Deterministic timeline story (3.7)
    timeline_story = _build_timeline_story(events)

    # 9) Top-level calibrated scores summary for frontend / judges
    calibrated_scores = [
        {
            "id": h.get("id"),
            "title": h.get("title"),
            "raw_score": float(next(
                (r.get("score") for r in refined if r.get("id") == h.get("id")),
                h.get("score", 0.0),
            )),
            "normalised_score": h.get("normalised_score"),
            "calibrated_score": h.get("calibrated_score"),
        }
        for h in calibrated_hypotheses
    ]

    return {
        "hypotheses": calibrated_hypotheses,
        "llm_commentary": commentary,
        "llm_model": "gemini-1.5-flash",
        "rule_based": rule_based,
        "similar_incidents": similar_incidents,
        "incident_summary": incident_summary,
        "recommended_actions": recommended_actions,
        "timeline_story": timeline_story,
        "incident_narrative": incident_narrative,
        "calibrated_scores": calibrated_scores,
        "calibrated_confidence": incident_summary["confidence"],
        "evidence_strength_report": evidence_strength_report,
        "contrastive_explanations": contrastive_explanations,
        "causal_graph": causal_graph,
    }