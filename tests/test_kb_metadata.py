"""Check trusted retrieval against the shipped KB, not hand-written metadata."""

from pathlib import Path

import pytest

from backend.rag.chunker import chunk_documents
from backend.rag.loader import _extract_metadata_fields, load_knowledge_base, load_markdown_file
from backend.rag.retriever import RetrievedChunk
from backend.services.checklist_builder import select_requirement_chunks
from backend.services.fee_lookup import select_fee_chunks
from backend.services.verification import verify_fee_sources, verify_requirement_sources


@pytest.fixture
def kb_chunks():
    kb_dir = Path(__file__).resolve().parents[1] / "knowledge_base"
    return [
        RetrievedChunk(chunk.text, chunk.metadata, 1.0, "knowledge_base")
        for chunk in chunk_documents(load_knowledge_base(str(kb_dir)))
    ]


@pytest.mark.parametrize("service,confidence", [("driving_license", "medium"), ("passport", "high")])
def test_shipped_requirements_have_canonical_service_and_provenance(kb_chunks, service, confidence):
    requirements = select_requirement_chunks(kb_chunks, service)
    assert verify_requirement_sources(requirements, service)
    assert all(chunk.metadata["confidence"] == confidence for chunk in requirements)
    assert all(chunk.metadata["source_url"].startswith("https://") for chunk in requirements)
    assert "CNIC" in "\n".join(chunk.text for chunk in requirements)


def test_shipped_driving_fees_are_found_but_never_promoted_to_verified(kb_chunks):
    matching, reliable = select_fee_chunks(kb_chunks, "driving_license")
    assert matching
    assert all(chunk.metadata["confidence"] == "medium" for chunk in matching)
    assert any("unverified" in chunk.text.casefold() for chunk in matching)
    assert not reliable
    assert not verify_fee_sources(reliable, "driving_license")
    _, passport_fees = select_fee_chunks(kb_chunks, "passport")
    assert verify_fee_sources(passport_fees, "passport")


@pytest.mark.parametrize("line,expected", [
    ("- **Confidence:** **Medium.**", "medium"),
    ("- **Confidence:** High — official source", "high"),
    ("Confidence: low", "low"),
    ("**Confidence**: **Low**", "low"),
    ("Confidence: unverified", None),
    ("No confidence label here", None),
])
def test_metadata_confidence_accepts_markdown_emphasis(line, expected):
    assert _extract_metadata_fields(line)["confidence"] == expected


@pytest.mark.parametrize("filename,service", [
    ("driving_license.md", "driving_license"),
    ("driving_license (1).md", "driving_license"),
    ("driving_license (2).md", "driving_license"),
    ("passport.md", "passport"),
    ("passport (12).md", "passport"),
    ("birth_certificate (1) (2).md", "birth_certificate"),
    ("other_service (regional).md", "other_service (regional)"),
    ("other_service_2026.md", "other_service_2026"),
])
def test_copy_counters_do_not_change_indexed_service_id(tmp_path, filename, service):
    path = tmp_path / filename
    path.write_text("## Required Documents\n- Original document.\n", encoding="utf-8")
    chunks = chunk_documents(load_markdown_file(path))
    assert chunks
    assert all(chunk.metadata["service"] == service for chunk in chunks)
    assert all(chunk.metadata["source_file"] == filename for chunk in chunks)


def test_copied_source_logs_are_still_excluded(tmp_path):
    for name in ("sources.md", "sources (1).md"):
        (tmp_path / name).write_text("## Research log\nNot service guidance.\n", encoding="utf-8")
    assert load_knowledge_base(str(tmp_path)) == []
