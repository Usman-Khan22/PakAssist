"""
Loads the Markdown knowledge base into RagDocument objects, one per
section (## heading), preserving the file's Metadata block (authority,
source URL, confidence) so every section inherits it.

Section-per-document (rather than whole-file) is what makes queries like
"what documents do I need" retrieve the "Required documents" section
specifically, instead of the whole service page.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

HEADING_RE = re.compile(r"^##\s+(.*)$", re.MULTILINE)
URL_RE = re.compile(r"https?://\S+")
CONFIDENCE_RE = re.compile(r"confidence[:\s]*[-*]*\s*(\w+)", re.IGNORECASE)


@dataclass
class RagDocument:
    """One retrievable unit before chunking (typically one Markdown section)."""

    text: str
    source_file: str
    service: str
    section: str
    source_url: Optional[str] = None
    confidence: Optional[str] = None
    document_type: str = "knowledge_base"
    extra: Dict = field(default_factory=dict)


def _split_sections(raw_text: str) -> List[tuple]:
    """Split a markdown file on level-2 (##) headings. Returns [(heading, body), ...]."""
    matches = list(HEADING_RE.finditer(raw_text))
    if not matches:
        return [("Full document", raw_text.strip())]

    sections = []
    for i, m in enumerate(matches):
        heading = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
        body = raw_text[start:end].strip()
        if body:
            sections.append((heading, body))
    return sections


def _extract_metadata_fields(metadata_section_text: str) -> Dict[str, Optional[str]]:
    """Pull a source URL and confidence rating out of the file's Metadata section."""
    url_match = URL_RE.search(metadata_section_text)
    conf_match = CONFIDENCE_RE.search(metadata_section_text)
    return {
        "source_url": url_match.group(0) if url_match else None,
        "confidence": conf_match.group(1).lower() if conf_match else None,
    }


def load_markdown_file(path: Path) -> List[RagDocument]:
    """Parse one knowledge-base markdown file into a list of RagDocuments."""
    raw_text = path.read_text(encoding="utf-8")
    service = path.stem  # e.g. "passport"
    sections = _split_sections(raw_text)

    # Pull file-level metadata (authority/source_url/confidence) from the
    # "Metadata" section, if present, and apply it to every other section.
    file_meta = {"source_url": None, "confidence": None}
    for heading, body in sections:
        if heading.strip().lower() == "metadata":
            file_meta = _extract_metadata_fields(body)
            break

    documents = []
    for heading, body in sections:
        if heading.strip().lower() == "metadata":
            continue  # metadata itself isn't useful to retrieve as an answer chunk
        documents.append(
            RagDocument(
                text=f"{heading}\n{body}",
                source_file=path.name,
                service=service,
                section=heading,
                source_url=file_meta["source_url"],
                confidence=file_meta["confidence"],
                document_type="knowledge_base",
            )
        )
    return documents


def load_knowledge_base(kb_dir: str) -> List[RagDocument]:
    """Load every .md file in the knowledge base directory."""
    kb_path = Path(kb_dir)
    if not kb_path.exists():
        raise FileNotFoundError(f"Knowledge base directory not found: {kb_dir}")

    documents: List[RagDocument] = []
    for md_file in sorted(kb_path.glob("*.md")):
        if md_file.name.lower() == "sources.md":
            continue  # a log of URLs, not user-facing service content
        documents.extend(load_markdown_file(md_file))
    return documents
