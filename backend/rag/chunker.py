"""
Turns RagDocuments (one per section) into RagChunks ready for embedding.

Kept deliberately simple: a section that already fits within max_chars
becomes exactly one chunk (this is what makes "Required documents" style
queries retrieve cleanly). Only sections longer than max_chars get split
further, on paragraph boundaries with a small overlap for continuity.
"""

from dataclasses import dataclass
from typing import Dict, List

from backend.rag.loader import RagDocument


@dataclass
class RagChunk:
    text: str
    metadata: Dict


def _split_long_text(text: str, max_chars: int, overlap: int) -> List[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_chars:
            current = f"{current}\n\n{para}" if current else para
        else:
            if current:
                chunks.append(current)
            # start new chunk, carrying a small overlap from the tail of the last one
            carry = current[-overlap:] if overlap and current else ""
            current = f"{carry}\n\n{para}" if carry else para

    if current:
        chunks.append(current)

    # Fallback: a single paragraph longer than max_chars — hard split it.
    final: List[str] = []
    for c in chunks:
        if len(c) <= max_chars:
            final.append(c)
        else:
            for i in range(0, len(c), max_chars - overlap):
                final.append(c[i : i + max_chars])
    return final


def chunk_documents(
    documents: List[RagDocument],
    max_chars: int = 800,
    overlap: int = 100,
) -> List[RagChunk]:
    """Chunk a list of RagDocuments, preserving each one's metadata on every chunk."""
    chunks: List[RagChunk] = []

    for doc in documents:
        pieces = (
            [doc.text]
            if len(doc.text) <= max_chars
            else _split_long_text(doc.text, max_chars, overlap)
        )
        for piece in pieces:
            chunks.append(
                RagChunk(
                    text=piece,
                    metadata={
                        "source_file": doc.source_file,
                        "service": doc.service,
                        "section": doc.section,
                        "source_url": doc.source_url,
                        "confidence": doc.confidence,
                        "document_type": doc.document_type,
                    },
                )
            )
    return chunks
