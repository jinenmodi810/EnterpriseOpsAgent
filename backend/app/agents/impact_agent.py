# backend/app/agents/impact_agent.py

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional


def _parse_time(ts: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def _compute_severity(num_critical: int, num_errors: int, total: int) -> str:
    """
    Very simple severity scale based on counts of critical/error events.
    You can refine this later.
    """
    if total == 0:
        return "unknown"

    critical_ratio = num_critical / total
    error_ratio = num_errors / total

    if critical_ratio > 0.2 or num_critical >= 3:
        return "critical"
    if error_ratio > 0.2 or num_errors >= 3:
        return "high"
    if num_errors > 0:
        return "medium"
    return "low"


def analyze_impact(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute a simple impact and risk summary from the event timeline.

    Input format is the same dict produced by build_timeline_from_dataframe:
      {
          "time": "...",
          "message": "...",
          "event_type": "...",
          "phase": "...",
          "source": "...",
          "level": "..."
      }
    """

    total_events = len(events)
    if total_events == 0:
        return {
            "severity": "unknown",
            "duration_minutes": 0.0,
            "num_events": 0,
            "num_critical": 0,
            "num_errors": 0,
            "user_impact_summary": "No events found in the incident timeline.",
            "key_signals": [],
        }

    # Convert times
    times: List[datetime] = []
    for e in events:
        t = _parse_time(e.get("time", ""))
        if t is not None:
            times.append(t)

    if times:
        duration_minutes = (max(times) - min(times)).total_seconds() / 60.0
    else:
        duration_minutes = 0.0

    num_critical = 0
    num_errors = 0
    candidate_user_impact_messages: List[str] = []
    key_signals: List[str] = []

    for e in events:
        level = (e.get("level") or "").lower()
        msg = e.get("message", "")
        etype = (e.get("event_type") or "").lower()

        if level == "critical":
            num_critical += 1
        if level == "error" or "error" in msg.lower():
            num_errors += 1

        # Heuristics for user-facing impact messages
        if any(
            phrase in msg.lower()
            for phrase in [
                "user",
                "customer",
                "unable to",
                "failed to",
                "500 error",
                "service unavailable",
            ]
        ):
            candidate_user_impact_messages.append(msg)

        # Key signals to surface in the UI
        if etype in {"alert", "error"} or level in {"critical", "error"}:
            key_signals.append(msg)

    severity = _compute_severity(num_critical, num_errors, total_events)

    if candidate_user_impact_messages:
        user_impact_summary = (
            "Detected probable user-facing impact based on the following signals: "
            + "; ".join(candidate_user_impact_messages[:3])
        )
    else:
        user_impact_summary = (
            "Impact appears to be mostly internal to the system. No explicit user-facing failures detected."
        )

    return {
        "severity": severity,
        "duration_minutes": round(duration_minutes, 1),
        "num_events": total_events,
        "num_critical": num_critical,
        "num_errors": num_errors,
        "user_impact_summary": user_impact_summary,
        "key_signals": key_signals[:10],
    }