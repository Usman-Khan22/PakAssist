import pytest

pytest.importorskip("sentence_transformers")

from backend.rag.embeddings import embed_texts


def test_embed_texts_returns_normalized_vectors():
    vectors = embed_texts(["What documents do I need for a driving license?", "hello"])

    assert vectors.shape[0] == 2
    assert vectors.shape[1] == 384  # MiniLM-L6-v2 output dim

    norms = (vectors**2).sum(axis=1) ** 0.5
    for n in norms:
        assert abs(n - 1.0) < 1e-3


def test_embed_texts_empty_input():
    vectors = embed_texts([])
    assert vectors.shape[0] == 0
