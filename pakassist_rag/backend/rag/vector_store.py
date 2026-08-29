"""
Minimal FAISS wrapper.

Uses a flat inner-product index over L2-normalized vectors (== cosine
similarity), which is plenty for a hackathon-scale knowledge base. Texts and
metadata are kept alongside the index in a parallel Python list and
pickled next to the FAISS index file, so nothing beyond FAISS + pickle is
required. This class is the only place that knows about FAISS, so it can be
swapped for another vector store later without touching the rest of the
pipeline.
"""

import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np


class FaissVectorStore:
    def __init__(self, dim: Optional[int] = None):
        self._dim = dim
        self._index = None
        self.texts: List[str] = []
        self.metadatas: List[Dict] = []

    def _ensure_index(self, dim: int):
        import faiss  # lazy import, only needed once a store is actually used

        if self._index is None:
            self._dim = dim
            self._index = faiss.IndexFlatIP(dim)

    def add(self, vectors: np.ndarray, texts: List[str], metadatas: List[Dict]) -> None:
        if len(vectors) == 0:
            return
        self._ensure_index(vectors.shape[1])
        self._index.add(vectors)
        self.texts.extend(texts)
        self.metadatas.extend(metadatas)

    def search(self, query_vector: np.ndarray, k: int = 5) -> List[Tuple[float, str, Dict]]:
        """Returns [(score, text, metadata), ...] sorted by descending score."""
        if self._index is None or self._index.ntotal == 0:
            return []

        k = min(k, self._index.ntotal)
        query_vector = query_vector.reshape(1, -1)
        scores, indices = self._index.search(query_vector, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append((float(score), self.texts[idx], self.metadatas[idx]))
        return results

    @property
    def size(self) -> int:
        return 0 if self._index is None else self._index.ntotal

    def save(self, directory: str) -> None:
        import faiss

        out_dir = Path(directory)
        out_dir.mkdir(parents=True, exist_ok=True)
        if self._index is not None:
            faiss.write_index(self._index, str(out_dir / "index.faiss"))
        with open(out_dir / "store.pkl", "wb") as f:
            pickle.dump({"texts": self.texts, "metadatas": self.metadatas, "dim": self._dim}, f)

    @classmethod
    def load(cls, directory: str) -> "FaissVectorStore":
        import faiss

        in_dir = Path(directory)
        index_path = in_dir / "index.faiss"
        store_path = in_dir / "store.pkl"
        if not index_path.exists() or not store_path.exists():
            raise FileNotFoundError(f"No saved vector store found at {directory}")

        with open(store_path, "rb") as f:
            data = pickle.load(f)

        store = cls(dim=data["dim"])
        store._index = faiss.read_index(str(index_path))
        store.texts = data["texts"]
        store.metadatas = data["metadatas"]
        return store
