# backend/app/agents/forensic_agent.py

from typing import List, Dict


def _score_keyword(message: str, keywords: List[str]) -> int:
    """
    Helper to count how many of the given keywords appear in the message.
    """
    m = message.lower()
    return sum(1 for kw in keywords if kw in m)


def generate_root_cause_hypotheses(events: List[Dict]) -> List[Dict]:
    """
    Very lightweight "root cause" agent.

    It inspects the timeline events and produces a few candidate hypotheses
    with simple rule-based scores. Later we can replace the internals with
    Gemini or another LLM, but the interface can stay the same.
    """

    if not events:
        return []

    # Aggregate evidence from all messages
    network_score = 0
    dependency_score = 0
    capacity_score = 0
    app_bug_score = 0

    for ev in events:
        msg = str(ev.get("message", "")).lower()
        src = str(ev.get("source", "")).lower()
        evt_type = str(ev.get("event_type", "")).lower()

        network_score += _score_keyword(
            msg,
            ["timeout", "connection reset", "dns", "network", "latency"],
        )

        dependency_score += _score_keyword(
            msg,
            ["payments-service", "database", "redis", "kafka", "upstream"],
        )

        capacity_score += _score_keyword(
            msg,
            ["cpu", "memory", "disk", "saturation", "pod", "throttle"],
        )

        app_bug_score += _score_keyword(
            msg,
            ["nullpointer", "stack trace", "exception", "bug", "deploy"],
        )

        # Extra weight for alerts and errors
        if evt_type in {"alert", "error"} or "critical" in msg:
            capacity_score += 1 if "cpu" in msg or "memory" in msg else 0
            network_score += 1 if "timeout" in msg else 0

        # If the source is clearly infra / platform, slightly bias capacity
        if src in {"infra", "platform"}:
            capacity_score += 1

    # Build hypotheses list
    raw_hypotheses: List[Dict] = []

    raw_hypotheses.append(
        {
            "id": "H1",
            "title": "Network or connectivity issue between services",
            "score": network_score,
            "explanation": (
                "Multiple messages mention timeouts, network terms, or high latency. "
                "This suggests a possible network or connectivity problem between services."
            ),
        }
    )

    raw_hypotheses.append(
        {
            "id": "H2",
            "title": "Downstream dependency or external service failure",
            "score": dependency_score,
            "explanation": (
                "Logs reference specific downstream components such as databases or payment services. "
                "This points to a dependency outage or regression."
            ),
        }
    )

    raw_hypotheses.append(
        {
            "id": "H3",
            "title": "Infrastructure capacity or resource saturation",
            "score": capacity_score,
            "explanation": (
                "Alerts or logs indicate high CPU, memory, or pod usage. "
                "This suggests capacity issues, autoscaling problems, or noisy neighbours."
            ),
        }
    )

    raw_hypotheses.append(
        {
            "id": "H4",
            "title": "Application code bug or faulty deployment",
            "score": app_bug_score,
            "explanation": (
                "Error messages or comments reference exceptions, stack traces, or recent deployments. "
                "This is consistent with an application bug or bad release."
            ),
        }
    )

    # Filter out hypotheses with zero evidence
    raw_hypotheses = [h for h in raw_hypotheses if h["score"] > 0]

    if not raw_hypotheses:
        return [
            {
                "id": "H_generic",
                "title": "Insufficient evidence for a specific root cause",
                "confidence": 0.2,
                "explanation": (
                    "The current logs do not strongly point to a single class of issue. "
                    "More detailed logs or runbook information would help refine hypotheses."
                ),
            }
        ]

    # Convert scores to simple confidences between 0 and 1
    max_score = max(h["score"] for h in raw_hypotheses) or 1
    hypotheses: List[Dict] = []
    for h in sorted(raw_hypotheses, key=lambda x: x["score"], reverse=True):
        confidence = h["score"] / max_score
        hypotheses.append(
            {
                "id": h["id"],
                "title": h["title"],
                "confidence": round(float(confidence), 2),
                "explanation": h["explanation"],
            }
        )

    return hypotheses