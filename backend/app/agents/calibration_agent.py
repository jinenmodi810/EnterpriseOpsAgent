# backend/app/agents/calibration_agent.py

from typing import List, Dict, Any, Tuple
import math


def score_normalisation(hypotheses: List[Dict[str, Any]]) -> List[float]:
    """
    Normalise raw hypothesis scores into [0, 1] while preserving ordering.
    Handles missing or out-of-range scores defensively.
    """
    if not hypotheses:
        return []

    raw_scores = []
    for h in hypotheses:
        try:
            s = float(h.get("score", 0.0))
        except (TypeError, ValueError):
            s = 0.0
        # Clamp to [0, 1] first (defensive)
        s = max(0.0, min(1.0, s))
        raw_scores.append(s)

    max_s = max(raw_scores)
    min_s = min(raw_scores)

    # If all scores are the same:
    # - if they are > 0, treat all as high evidence (set to 1.0)
    # - if they are 0, keep as 0
    if max_s == min_s:
        if max_s > 0:
            return [1.0 for _ in raw_scores]
        return raw_scores

    normalised = [(s - min_s) / (max_s - min_s) for s in raw_scores]
    return normalised


def softmax_confidence_adjustment(normalised_scores: List[float]) -> List[float]:
    """
    Convert normalised scores into a softmax distribution.
    This:
      - keeps scores in (0,1)
      - avoids overconfidence when several hypotheses are strong.
    """
    if not normalised_scores:
        return []

    # Standard softmax with numerical stability
    max_input = max(normalised_scores)
    exps = [math.exp(s - max_input) for s in normalised_scores]
    total = sum(exps)
    if total == 0:
        return [0.0 for _ in normalised_scores]

    return [e / total for e in exps]


def confidence_penalty(
    hypotheses: List[Dict[str, Any]],
    events: List[Dict[str, Any]],
    base_primary_confidence: float,
    softmax_primary_confidence: float,
) -> Tuple[float, Dict[str, Any]]:
    """
    Apply calibration penalties:
      - short timelines → reduce confidence
      - many high-scoring hypotheses → reduce confidence
    Returns:
      final_primary_confidence, evidence_strength_report
    """
    n_events = len(events)

    # Timeline length penalty
    if n_events == 0:
        length_factor = 0.5
    elif n_events < 5:
        length_factor = 0.7
    elif n_events < 10:
        length_factor = 0.85
    else:
        length_factor = 1.0

    # Multiple strong hypotheses penalty
    num_high = sum(1 for h in hypotheses if float(h.get("score", 0.0)) >= 0.8)
    if num_high > 1:
        multi_factor = 0.9
    else:
        multi_factor = 1.0

    final_conf = softmax_primary_confidence * length_factor * multi_factor

    evidence_strength_report: Dict[str, Any] = {
        "timeline_length": n_events,
        "raw_primary_confidence": round(float(base_primary_confidence), 2),
        "softmax_primary_confidence": round(float(softmax_primary_confidence), 2),
        "timeline_length_penalty_factor": round(length_factor, 2),
        "multiple_high_hypotheses": num_high,
        "multiple_high_penalty_factor": round(multi_factor, 2),
        "final_primary_confidence": round(final_conf, 2),
    }

    return final_conf, evidence_strength_report


def calibrate_hypotheses(
    hypotheses: List[Dict[str, Any]],
    events: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], float, Dict[str, Any]]:
    """
    End-to-end calibration:
      1) Normalise scores into [0,1]
      2) Softmax into probabilities
      3) Apply confidence penalties
      4) Attach calibrated_score and normalised_score to each hypothesis

    Returns:
      calibrated_hypotheses, calibrated_primary_confidence, evidence_strength_report
    """
    if not hypotheses:
        empty_report = {
            "timeline_length": len(events),
            "raw_primary_confidence": 0.0,
            "softmax_primary_confidence": 0.0,
            "timeline_length_penalty_factor": 0.0,
            "multiple_high_hypotheses": 0,
            "multiple_high_penalty_factor": 0.0,
            "final_primary_confidence": 0.0,
        }
        return [], 0.0, empty_report

    # 1) Normalise raw scores
    normalised = score_normalisation(hypotheses)

    # 2) Softmax probabilities
    softmax_probs = softmax_confidence_adjustment(normalised)

    # Primary hypothesis index based on original (refined) score
    primary_index = max(
        range(len(hypotheses)),
        key=lambda i: float(hypotheses[i].get("score", 0.0)),
    )
    base_primary_conf = float(hypotheses[primary_index].get("score", 0.0))
    softmax_primary_conf = softmax_probs[primary_index]

    # 3) Global confidence penalties
    final_conf, evidence_strength_report = confidence_penalty(
        hypotheses=hypotheses,
        events=events,
        base_primary_confidence=base_primary_conf,
        softmax_primary_confidence=softmax_primary_conf,
    )

    # 4) Attach calibrated fields to each hypothesis
    calibrated: List[Dict[str, Any]] = []
    for h, n, p in zip(hypotheses, normalised, softmax_probs):
        item = dict(h)
        item["normalised_score"] = round(float(n), 3)
        item["calibrated_score"] = round(float(p), 3)
        calibrated.append(item)

    return calibrated, float(final_conf), evidence_strength_report