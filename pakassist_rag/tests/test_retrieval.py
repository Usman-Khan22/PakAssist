import pytest

pytest.importorskip("sentence_transformers")
pytest.importorskip("faiss")

from backend.rag.chunker import chunk_documents
from backend.rag.embeddings import embed_texts
from backend.rag.loader import load_knowledge_base
from backend.rag.retriever import Retriever
from backend.rag.vector_store import FaissVectorStore


@pytest.fixture(scope="module")
def retriever(kb_dir) -> Retriever:
    """Build an in-memory retriever from the stand-in knowledge base."""
    docs = load_knowledge_base(kb_dir)
    chunks = chunk_documents(docs)
    vectors = embed_texts([c.text for c in chunks])

    store = FaissVectorStore()
    store.add(vectors=vectors, texts=[c.text for c in chunks], metadatas=[c.metadata for c in chunks])
    return Retriever(kb_store=store)


def test_driving_license_required_documents_query(retriever):
    results = retriever.retrieve("What documents are required for a driving license?", top_k=3)
    assert results, "expected at least one relevant chunk"
    assert results[0].metadata["service"] == "driving_license"


def test_passport_requirements_query(retriever):
    results = retriever.retrieve("What are the requirements for a Pakistani passport?", top_k=3)
    assert results, "expected at least one relevant chunk"
    assert results[0].metadata["service"] == "passport"


def test_unknown_query_does_not_confidently_match(retriever):
    """An unrelated query should either return nothing or only weak matches,
    which is what lets the Knowledge Agent fall back to the safe message
    instead of fabricating an answer."""
    results = retriever.retrieve(
        "What is the best recipe for biryani?",
        top_k=3,
        min_score=0.0,  # look at raw scores directly for this assertion
    )
    if results:
        assert results[0].score < 0.5
