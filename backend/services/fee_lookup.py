"""Grounded fee request detection and trusted-section selection."""

from backend.rag.retriever import RetrievedChunk


FEE_NOT_FOUND_MESSAGE = (
    "I couldn't find reliable, verified fee information for this service in "
    "the current knowledge base."
)

FEE_SYSTEM_PROMPT = """You are PakAssist's grounded Fee Lookup formatter.

Answer using ONLY the retrieved trusted fee context.

Rules:
- Never estimate, calculate, update, or invent a fee.
- Preserve every fee category and distinction present in the context, including
  validity, urgency, document type, page count, surcharge, and effective date.
- Preserve warnings about additional charges and re-confirming current fees.
- If the citizen did not specify a category, present the available distinctions
  instead of choosing one for them.
- Keep the response concise but do not collapse distinct fee categories into a
  single amount.
"""

_FEE_QUERY_TERMS = ("fee", "fees", "cost", "price", "how much")


def is_fee_request(intent: str, query: str) -> bool:
    text = f"{intent} {query}".casefold()
    return any(term in text for term in _FEE_QUERY_TERMS)


def fee_retrieval_query(service_type: str, query: str) -> str:
    service = service_type.replace("_", " ")
    return f"{service} verified official fee schedule categories amounts cost {query}"


def select_fee_chunks(
    chunks: list[RetrievedChunk], service_type: str
) -> tuple[list[RetrievedChunk], list[RetrievedChunk]]:
    """Return all matching fee chunks and the high-confidence subset."""
    matching = [
        chunk
        for chunk in chunks
        if chunk.origin == "knowledge_base"
        and chunk.metadata.get("service") == service_type
        and "fee" in str(chunk.metadata.get("section", "")).casefold()
    ]
    reliable = [
        chunk
        for chunk in matching
        if str(chunk.metadata.get("confidence", "")).casefold() == "high"
        and "unverified" not in chunk.text.casefold()
    ]
    return matching, reliable

