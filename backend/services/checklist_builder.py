"""Grounded checklist request detection and formatting rules."""

from backend.rag.retriever import RetrievedChunk


CHECKLIST_NOT_FOUND_MESSAGE = (
    "I couldn't find trusted checklist requirements for this service in the "
    "current knowledge base."
)

CHECKLIST_SYSTEM_PROMPT = """You are PakAssist's Checklist Builder.

Use ONLY the retrieved trusted context. Transform its required-document or
what-to-bring information into a concise actionable checklist.

Rules:
- Start with "Required documents:".
- Format every supported item as a line beginning with "☐".
- Preserve distinctions such as adult/minor, new/renewal, conditional items,
  and province-specific requirements when the context contains them.
- Preserve every uncertainty or instruction to confirm locally.
- Do not add requirements from general knowledge or infer missing items.
- If the context is incomplete, say so plainly.
"""

_CHECKLIST_QUERY_TERMS = (
    "checklist",
    "what documents",
    "which documents",
    "required documents",
    "documents do i need",
    "document requirements",
    "what do i need",
    "what should i take",
    "what should i bring",
    "what do i take",
    "what do i bring",
)


def is_checklist_request(intent: str, query: str) -> bool:
    text = f"{intent} {query}".casefold()
    return any(term in text for term in _CHECKLIST_QUERY_TERMS)


def checklist_retrieval_query(service_type: str, query: str) -> str:
    service = service_type.replace("_", " ")
    return f"{service} required documents application checklist what to bring {query}"


def select_requirement_chunks(
    chunks: list[RetrievedChunk], service_type: str
) -> list[RetrievedChunk]:
    """Keep trusted required-document sections for the requested service."""
    return [
        chunk
        for chunk in chunks
        if chunk.origin == "knowledge_base"
        and chunk.metadata.get("service") == service_type
        and "required document" in str(chunk.metadata.get("section", "")).casefold()
    ]
