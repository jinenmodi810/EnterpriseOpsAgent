from typing import List, Dict, Any, Tuple
import math

import google.generativeai as genai

from ..core.config import settings

# From your list_models.py output: a valid embedding model
EMBEDDING_MODEL_NAME = "models/text-embedding-004"


def _configure_client() -> None:
    """
    Configure the Gemini client once using your API key.
    """
    if not settings.gemini_api_key:
        raise RuntimeError("Gemini API key not configured.")
    genai.configure(api_key=settings.gemini_api_key)


def _embed_text(text: str) -> List[float]:
    """
    Return embedding vector for a given text using Gemini embeddings.
    """
    _configure_client()
    result = genai.embed_content(
        model=EMBEDDING_MODEL_NAME,
        content=text,
    )
    # Python client returns a dict with "embedding"
    return result["embedding"]


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """
    Cosine similarity between two vectors.
    """
    if not a or not b or len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


# In-memory “knowledge base” of past incidents.
_RAW_KB: List[Dict[str, str]] = [
    {
        "id": "INC_PAYMENTS_TIMEOUT",
        "title": "Checkout outage due to payments-service timeouts",
        "summary": (
            "Checkout API experienced high latency and error rates because the payments-service "
            "was timing out. Restarting the payments container and scaling checkout pods "
            "resolved the incident."
        ),
    },
    {
        "id": "INC_DB_CONNECTION_POOL",
        "title": "Database connection pool exhaustion in orders DB",
        "summary": (
            "Order creation failed intermittently when the PostgreSQL connection pool was exhausted. "
            "Misconfigured pool size combined with a traffic spike caused timeouts and 5xx errors."
        ),
    },
    {
        "id": "INC_K8S_AUTOSCALER",
        "title": "Kubernetes autoscaler misconfiguration causing CPU saturation",
        "summary": (
            "Pods for a critical service hit 90 percent CPU due to an autoscaler minReplicas setting "
            "being too low. Updating the autoscaler configuration and increasing pod count "
            "stabilised the system."
        ),
    },
]

# Cache: [(kb_item, embedding_vector)]
_KB_EMBEDDINGS: List[Tuple[Dict[str, str], List[float]]] = []


def _ensure_kb_embeddings_loaded() -> None:
    """
    Compute and cache embeddings for the KB summaries on first use.
    If embedding fails for an item, it is skipped.
    """
    global _KB_EMBEDDINGS
    if _KB_EMBEDDINGS:
        return

    enriched: List[Tuple[Dict[str, str], List[float]]] = []
    for item in _RAW_KB:
        summary = item["summary"]
        try:
            emb = _embed_text(summary)
            enriched.append((item, emb))
        except Exception:
            # If embedding fails, skip this KB entry to stay robust
            continue

    _KB_EMBEDDINGS = enriched


def find_similar_incidents(
    events: List[Dict[str, Any]],
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """
    Given the current incident events, return top_k similar incidents from the KB
    using Gemini embeddings and cosine similarity.

    Always fails safely: on any error it returns an empty list.
    """
    if not events:
        return []

    try:
        _ensure_kb_embeddings_loaded()
    except Exception:
        # Could not initialise embeddings – return no results, do not break API
        return []

    if not _KB_EMBEDDINGS:
        return []

    query_text = "\n".join(
        e.get("message", "") for e in events[:30] if e.get("message")
    ).strip()

    if not query_text:
        return []

    try:
        query_emb = _embed_text(query_text)
    except Exception:
        return []

    scored: List[Tuple[float, Dict[str, str]]] = []
    for item, emb in _KB_EMBEDDINGS:
        score = _cosine_similarity(query_emb, emb)
        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]

    results: List[Dict[str, Any]] = []
    for score, item in top:
        results.append(
            {
                "id": item["id"],
                "title": item["title"],
                "summary": item["summary"],
                "similarity": round(float(score), 3),
            }
        )

    return results