from typing import List, Dict, Any

from .embedding_agent import get_text_embedding
from .vector_store import get_global_incident_store


def _build_timeline_text(events: List[Dict[str, Any]]) -> str:
    """
    Convert a list of events into a single text block for embedding.
    We focus on time and message fields which capture most semantics.
    """
    lines = []
    for e in events[:50]:  # safety cap
        time = e.get("time") or e.get("timestamp") or ""
        msg = e.get("message") or ""
        if msg:
            lines.append(f"{time} - {msg}")
    return "\n".join(lines)


def find_similar_incidents(
    events: List[Dict[str, Any]],
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """
    Embed the incident timeline and retrieve top_k similar incidents
    from the KB vector store.

    Returns a list of:
    {
      "id": "...",
      "title": "...",
      "summary": "...",
      "similarity": 0.0-1.0
    }
    """
    if not events:
        return []

    # Build input text and embed
    timeline_text = _build_timeline_text(events)
    query_vec = get_text_embedding(timeline_text)

    # Search vector store
    store = get_global_incident_store()
    matches = store.search(query_vec, top_k=top_k)

    # Normalise similarity into [0, 1] (cosine is already in [-1,1])
    results: List[Dict[str, Any]] = []
    for score, meta in matches:
        # Clamp and scale from [-1, 1] to [0, 1]
        clipped = max(min(score, 1.0), -1.0)
        norm_score = (clipped + 1.0) / 2.0

        results.append(
            {
                "id": meta.get("id"),
                "title": meta.get("title"),
                "summary": meta.get("summary"),
                "similarity": round(norm_score, 3),
            }
        )

    return results