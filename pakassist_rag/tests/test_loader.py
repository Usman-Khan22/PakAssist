from backend.rag.loader import load_knowledge_base


def test_loads_all_stand_in_services(kb_dir):
    docs = load_knowledge_base(kb_dir)
    services = {d.service for d in docs}

    assert "passport" in services
    assert "driving_license" in services
    # sources.md is a log, not a service doc, and must be excluded
    assert "sources" not in services


def test_sections_carry_file_level_metadata(kb_dir):
    docs = load_knowledge_base(kb_dir)
    passport_docs = [d for d in docs if d.service == "passport"]

    assert len(passport_docs) > 1  # split into multiple sections
    for d in passport_docs:
        assert d.confidence == "high"
        assert d.source_url and d.source_url.startswith("http")
        assert d.document_type == "knowledge_base"


def test_required_documents_section_is_isolated(kb_dir):
    docs = load_knowledge_base(kb_dir)
    required_docs_sections = [
        d for d in docs if d.service == "driving_license" and "required documents" in d.section.lower()
    ]
    assert len(required_docs_sections) == 1
    assert "CNIC" in required_docs_sections[0].text
