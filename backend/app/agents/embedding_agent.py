from typing import List
import google.generativeai as genai

from ..core.config import settings

# Correct model name from your list_models output
EMBEDDING_MODEL_NAME = "models/text-embedding-004"


def _ensure_client_configured() -> None:
    """
    Configure the Gemini client. Raises RuntimeError if the API key
    is missing to make failures explicit.
    """
    if not settings.gemini_api_key:
        raise RuntimeError("Gemini API key not configured for embeddings.")
    genai.configure(api_key=settings.gemini_api_key)


def get_text_embedding(text: str) -> List[float]:
    """
    Get a dense embedding vector for a given text using Gemini embeddings.
    Returns a list[float] suitable for vector search.
    """
    _ensure_client_configured()

    # The client returns either 'embedding' or 'values' depending on version;
    # we normalise to a plain python list of floats.
    result = genai.embed_content(
        model=EMBEDDING_MODEL_NAME,
        content=text,
    )

    # Newer client returns {'embedding': {'values': [...]}}
    embedding = result.get("embedding") or result
    values = embedding.get("values") if isinstance(embedding, dict) else embedding

    if not isinstance(values, list):
        raise RuntimeError("Unexpected embedding format from Gemini.")

    return [float(x) for x in values]