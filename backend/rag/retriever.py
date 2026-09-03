"""
Clean retriever interface used by the Knowledge Agent.

Combines two sources:
  1. the persisted knowledge-base FAISS index (built offline via
     scripts/build_index.py)
  2. an in-memory, per-session FAISS index for whatever the user uploaded
     this turn (never persisted to disk — it's request-scoped)

Results from both are returned together but stay distinguishable via
metadata["document_type"] / the returned "origin" field, so the Knowledge
Agent (and eventually the UI) can show which parts of an answer came from
the trusted knowledge base versus the user's own files.
"""

import os
from threading import RLock
from dataclasses import dataclass
from typing import Dict, List, Optional

from backend.rag.chunker import RagChunk, chunk_documents
from backend.rag.embeddings import embed_texts
from backend.rag.loader import RagDocument
from backend.rag.vector_store import FaissVectorStore


@dataclass
class RetrievedChunk:
    text: str
    metadata: Dict
    score: float
    origin: str  # "knowledge_base" | "user_upload"


class Retriever:
    def __init__(self, kb_store: FaissVectorStore):
        self.kb_store = kb_store
        self.upload_stores: Dict[str, FaissVectorStore] = {}
        self._upload_lock = RLock()

    @classmethod
    def from_index_dir(cls, index_dir: str) -> "Retriever":
        return cls(kb_store=FaissVectorStore.load(index_dir))

    @staticmethod
    def _valid_thread_id(thread_id: Optional[str]) -> str:
        if not isinstance(thread_id, str) or not thread_id.strip():
            raise ValueError("A valid thread_id is required for user-upload content.")
        return thread_id

    def add_user_content(
        self, documents: List[RagDocument], *, thread_id: Optional[str]
    ) -> None:
        """Embed and index user-uploaded content for one process-local thread."""
        if not documents:
            return
        thread_id = self._valid_thread_id(thread_id)

        chunks = chunk_documents(documents)
        vectors = embed_texts([c.text for c in chunks])
        with self._upload_lock:
            store = self.upload_stores.setdefault(thread_id, FaissVectorStore())
            store.add(
                vectors=vectors,
                texts=[c.text for c in chunks],
                metadatas=[c.metadata for c in chunks],
            )

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        include_user_files: bool = True,
        min_score: Optional[float] = None,
        thread_id: Optional[str] = None,
        prefer_user_files: bool = False,
    ) -> List[RetrievedChunk]:
        top_k = top_k or int(os.getenv("RAG_TOP_K", "5"))
        min_score = min_score if min_score is not None else float(os.getenv("RAG_MIN_SCORE", "0.15"))

        query_vector = embed_texts([query])[0]

        official_raw = list(self.kb_store.search(query_vector, k=top_k))
        upload_raw = []
        if include_user_files and thread_id:
            with self._upload_lock:
                upload_store = self.upload_stores.get(thread_id)
                if upload_store is not None:
                    upload_raw = list(upload_store.search(query_vector, k=top_k))

        official_results = [
            RetrievedChunk(
                text=text,
                metadata=meta,
                score=score,
                origin="knowledge_base",
            )
            for score, text, meta in official_raw
            if score >= min_score
        ]
        upload_results = [
            RetrievedChunk(
                text=text,
                metadata=meta,
                score=score,
                origin="user_upload",
            )
            for score, text, meta in upload_raw
            if score >= min_score
        ]

        results = official_results + upload_results
        results.sort(key=lambda r: r.score, reverse=True)
        if prefer_user_files and upload_results and top_k > 0:
            reserved = max(upload_results, key=lambda result: result.score)
            remaining = [result for result in results if result is not reserved]
            return [reserved, *remaining[: top_k - 1]]
        return results[:top_k]
