from backend.rag.chunker import chunk_documents
from backend.rag.loader import RagDocument, load_knowledge_base


def test_short_section_becomes_single_chunk(kb_dir):
    docs = load_knowledge_base(kb_dir)
    chunks = chunk_documents(docs, max_chars=800, overlap=100)

    # every chunk must retain the metadata fields the spec requires
    for c in chunks:
        for key in ("source_file", "service", "section", "source_url", "confidence", "document_type"):
            assert key in c.metadata


def test_long_section_gets_split_with_overlap():
    long_text = "Heading\n" + ("Paragraph text goes here. " * 200)
    doc = RagDocument(
        text=long_text,
        source_file="fake.md",
        service="fake",
        section="Heading",
        source_url=None,
        confidence="low",
        document_type="knowledge_base",
    )

    chunks = chunk_documents([doc], max_chars=300, overlap=50)

    assert len(chunks) > 1
    for c in chunks:
        assert len(c.text) <= 300 + 5  # small tolerance for split boundaries
        assert c.metadata["service"] == "fake"
