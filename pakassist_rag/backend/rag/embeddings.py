"""
Thin wrapper around sentence-transformers/all-MiniLM-L6-v2.

Kept as a single lazily-loaded singleton so the (relatively slow) model load
only happens once per process, whether called from ingestion, retrieval,
or tests.
"""

import os
from typing import List, Optional

import numpy as np

_model = None
_model_name: Optional[str] = None

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def get_embedder(model_name: Optional[str] = None):
    """Return a cached SentenceTransformer instance."""
    global _model, _model_name

    model_name = model_name or os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL)

    if _model is None or _model_name != model_name:
        # Imported lazily so importing this module doesn't require the
        # (heavier) sentence-transformers package unless embedding is used.
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(model_name)
        _model_name = model_name

    return _model


def embed_texts(texts: List[str], model_name: Optional[str] = None) -> np.ndarray:
    """Embed a list of texts, L2-normalized so inner product == cosine similarity."""
    if not texts:
        return np.zeros((0, 384), dtype="float32")

    model = get_embedder(model_name)
    vectors = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (vectors / norms).astype("float32")
