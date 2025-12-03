from __future__ import annotations

from typing import List, Dict, Any, Tuple
from pathlib import Path
import json
import math

import numpy as np

from .embedding_agent import get_text_embedding


class IncidentVectorStore:
    """
    In-memory vector store for incident KB.
    Uses cosine similarity over Gemini embeddings.
    """

    def __init__(self) -> None:
        self._embeddings: np.ndarray | None = None  # shape: (n, d)
        self._metadata: List[Dict[str, Any]] = []

    @property
    def is_built(self) -> bool:
        return self._embeddings is not None and len(self._metadata) > 0

    def build_from_kb(self, kb_dir: Path) -> None:
        """
        Scan kb_dir for *.json incident files, embed them, and store vectors.
        """
        incident_files = sorted(kb_dir.glob("*.json"))
        if not incident_files:
            raise RuntimeError(f"No incident JSON files found in KB directory: {kb_dir}")

        embeddings: List[List[float]] = []
        metadata: List[Dict[str, Any]] = []

        for path in incident_files:
            with path.open("r", encoding="utf-8") as f:
                doc = json.load(f)

            # Build an embedding text that mixes title, summary, and tags
            title = doc.get("title", "")
            summary = doc.get("summary", "")
            tags = ", ".join(doc.get("tags", []))

            embed_text = f"Title: {title}\nSummary: {summary}\nTags: {tags}"
            vector = get_text_embedding(embed_text)

            embeddings.append(vector)
            metadata.append(doc)

        self._embeddings = np.array(embeddings, dtype="float32")
        self._metadata = metadata

    def _cosine_similarity(
        self, query_vec: np.ndarray, matrix: np.ndarray
    ) -> np.ndarray:
        """
        Compute cosine similarity between query_vec (d,) and matrix (n, d).
        """
        # Normalise
        q_norm = query_vec / (np.linalg.norm(query_vec) + 1e-8)
        m_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-8)
        # Cosine similarity is dot product of normalised vectors
        return m_norm @ q_norm

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 3,
    ) -> List[Tuple[float, Dict[str, Any]]]:
        """
        Return top_k incidents as (similarity_score, metadata) tuples.
        """
        if not self.is_built:
            raise RuntimeError("IncidentVectorStore has not been built yet.")

        q = np.array(query_embedding, dtype="float32")
        sims = self._cosine_similarity(q, self._embeddings)  # shape (n,)

        # Get top_k indices sorted by similarity descending
        idx_sorted = np.argsort(-sims)
        top_indices = idx_sorted[:top_k]

        results: List[Tuple[float, Dict[str, Any]]] = []
        for idx in top_indices:
            score = float(sims[idx])
            meta = self._metadata[int(idx)]
            results.append((score, meta))
        return results


# Module-level singleton for reuse
_vector_store: IncidentVectorStore | None = None


def get_global_incident_store() -> IncidentVectorStore:
    """
    Build (once) and return a global IncidentVectorStore instance.
    """
    global _vector_store
    if _vector_store is not None and _vector_store.is_built:
        return _vector_store

    # Determine KB dir: backend/kb/incidents from this file
    base_dir = Path(__file__).resolve().parents[2]  # .../backend
    kb_dir = base_dir / "kb" / "incidents"

    store = IncidentVectorStore()
    store.build_from_kb(kb_dir)
    _vector_store = store
    return store