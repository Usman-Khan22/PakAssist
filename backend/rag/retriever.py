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
        self.user_store: Optional[FaissVectorStore] = None  # built lazily, per session

    @classmethod
    def from_index_dir(cls, index_dir: str) -> "Retriever":
        return cls(kb_store=FaissVectorStore.load(index_dir))

    def add_user_content(self, documents: List[RagDocument]) -> None:
        """Embed and index user-uploaded content for this session only."""
        if not documents:
            return
        if self.user_store is None:
            self.user_store = FaissVectorStore()

        chunks = chunk_documents(documents)
        vectors = embed_texts([c.text for c in chunks])
        self.user_store.add(
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
    ) -> List[RetrievedChunk]:
        top_k = top_k or int(os.getenv("RAG_TOP_K", "5"))
        min_score = min_score if min_score is not None else float(os.getenv("RAG_MIN_SCORE", "0.15"))

        query_vector = embed_texts([query])[0]

        raw_results = list(self.kb_store.search(query_vector, k=top_k))
        if include_user_files and self.user_store is not None:
            raw_results += self.user_store.search(query_vector, k=top_k)

        results = [
            RetrievedChunk(
                text=text,
                metadata=meta,
                score=score,
                origin="user_upload" if meta.get("document_type", "").startswith("user_") else "knowledge_base",
            )
            for score, text, meta in raw_results
            if score >= min_score
        ]

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]
