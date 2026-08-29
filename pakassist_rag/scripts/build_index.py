"""
Rebuilds the knowledge-base FAISS index from the Markdown files in KB_DIR.

Usage:
    python scripts/build_index.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from backend.rag.chunker import chunk_documents
from backend.rag.embeddings import embed_texts
from backend.rag.loader import load_knowledge_base
from backend.rag.vector_store import FaissVectorStore

load_dotenv()


def main():
    kb_dir = os.getenv("KB_DIR", "knowledge_base")
    index_dir = os.getenv("KB_INDEX_DIR", "data/faiss_index")

    print(f"Loading knowledge base from: {kb_dir}")
    documents = load_knowledge_base(kb_dir)
    print(f"Loaded {len(documents)} sections from the knowledge base.")

    chunks = chunk_documents(documents)
    print(f"Produced {len(chunks)} chunks.")

    print("Embedding chunks (this loads the MiniLM model on first run)...")
    vectors = embed_texts([c.text for c in chunks])

    store = FaissVectorStore()
    store.add(vectors=vectors, texts=[c.text for c in chunks], metadatas=[c.metadata for c in chunks])
    store.save(index_dir)

    print(f"Saved index with {store.size} vectors to: {index_dir}")


if __name__ == "__main__":
    main()
