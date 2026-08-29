"""
Quick manual retrieval test against the built index — no Gemini call, just
FAISS + embeddings, so you can sanity-check retrieval quality on its own.

Usage:
    python scripts/query_test.py "What documents do I need for a driving license?"
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from backend.rag.retriever import Retriever

load_dotenv()


def main():
    if len(sys.argv) < 2:
        print('Usage: python scripts/query_test.py "your question here"')
        sys.exit(1)

    query = sys.argv[1]
    index_dir = os.getenv("KB_INDEX_DIR", "data/faiss_index")

    retriever = Retriever.from_index_dir(index_dir)
    results = retriever.retrieve(query)

    if not results:
        print("No relevant chunks found above the confidence threshold.")
        return

    for i, r in enumerate(results, start=1):
        print(f"\n--- Result {i} (score={r.score:.3f}, origin={r.origin}) ---")
        print(f"service={r.metadata.get('service')} section={r.metadata.get('section')}")
        print(f"source_url={r.metadata.get('source_url')} confidence={r.metadata.get('confidence')}")
        print(r.text[:300] + ("..." if len(r.text) > 300 else ""))


if __name__ == "__main__":
    main()
