"""
Knowledge Agent — replaces the "knowledge" placeholder node described in
PROJECT_CONTEXT.md with real retrieval + grounded generation.

Flow:
    state (user_input, optional uploaded_files)
        -> retrieve from knowledge base [+ any uploaded files, extracted first]
        -> if nothing relevant found: write the safe "couldn't find" message,
           WITHOUT calling Gemini (cheaper and removes a hallucination path)
        -> otherwise: build a source-attributed context block and ask Gemini
           to answer strictly from it
        -> write state["response"] and state["sources"]

Gemini calls use the same `google-genai` client and AFC-disable fix as the
Planner (see backend/rag/multimodal.py) — no tools, automatic function
calling explicitly disabled.
"""

import os
from pathlib import Path
from typing import List

from backend.graph.state import PakAssistState, SourceRef
from backend.rag.loader import RagDocument
from backend.rag.multimodal import extract_text_from_image, extract_text_from_pdf
from backend.rag.retriever import Retriever, RetrievedChunk

NO_CONTEXT_MESSAGE = (
    "I couldn't find reliable information for this request in the current "
    "knowledge base."
)

_GENERATION_SYSTEM_PROMPT = """You are PakAssist's Knowledge answer generator.

Rules you must follow:
- Answer using ONLY the information in the "Retrieved context" below.
- Do not invent, assume, or fill in any government requirement, fee, or
  process step that is not present in the retrieved context.
- If the context only partially answers the question, answer the part it
  supports and explicitly say what is missing rather than guessing.
- If a piece of context is marked low or medium confidence, say so plainly
  rather than presenting it as certain.
- Do not use your own general knowledge about Pakistani government
  services to fill gaps — if the context doesn't support a claim, don't
  make it.
- Keep the answer concise and directly useful to the citizen asking.
"""

_index_dir_retriever_cache = {}
_client = None


def _get_client():
    global _client
    if _client is None:
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        _client = genai.Client(api_key=api_key)
    return _client


def _get_retriever() -> Retriever:
    """Cache one Retriever per KB_INDEX_DIR so the FAISS index loads once."""
    index_dir = os.getenv("KB_INDEX_DIR", "data/faiss_index")
    if index_dir not in _index_dir_retriever_cache:
        _index_dir_retriever_cache[index_dir] = Retriever.from_index_dir(index_dir)
    return _index_dir_retriever_cache[index_dir]


def _extract_uploaded_files(file_paths: List[str]) -> List[RagDocument]:
    """Turn uploaded images/PDFs into RagDocuments via Gemini/PyMuPDF."""
    documents: List[RagDocument] = []

    for path_str in file_paths:
        path = Path(path_str)
        suffix = path.suffix.lower()

        if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
            text = extract_text_from_image(str(path))
            documents.append(
                RagDocument(
                    text=text,
                    source_file=path.name,
                    service="user_upload",
                    section="image",
                    document_type="user_image",
                )
            )
        elif suffix == ".pdf":
            for page_num, text, method in extract_text_from_pdf(str(path)):
                documents.append(
                    RagDocument(
                        text=text,
                        source_file=path.name,
                        service="user_upload",
                        section=f"page_{page_num}",
                        document_type="user_pdf",
                        extra={"extraction_method": method},
                    )
                )
        # other file types are out of scope for this milestone

    return documents


def _build_context_block(chunks: List[RetrievedChunk]) -> str:
    lines = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk.metadata
        label = meta.get("service") or meta.get("source_file") or "unknown"
        lines.append(
            f"[{i}] origin={chunk.origin} service={label} section={meta.get('section')} "
            f"confidence={meta.get('confidence', 'unknown')}\n{chunk.text}"
        )
    return "\n\n".join(lines)


def _chunks_to_source_refs(chunks: List[RetrievedChunk]) -> List[SourceRef]:
    seen = set()
    refs: List[SourceRef] = []
    for chunk in chunks:
        meta = chunk.metadata
        key = (meta.get("service"), meta.get("section"), chunk.origin)
        if key in seen:
            continue
        seen.add(key)
        service = meta.get("service") or meta.get("source_file") or "Uploaded file"
        label = f"{service.replace('_', ' ').title()} — {meta.get('section')}" if meta.get("section") else service
        refs.append(
            SourceRef(
                label=label,
                origin=chunk.origin,
                service=meta.get("service"),
                section=meta.get("section"),
                source_url=meta.get("source_url"),
                confidence=meta.get("confidence"),
            )
        )
    return refs


def _call_gemini(query: str, context_block: str) -> str:
    from google.genai import types

    client = _get_client()
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    prompt = f"Retrieved context:\n{context_block}\n\nCitizen's question:\n{query}"

    # No `tools=`, AFC explicitly disabled — same fix as the Planner.
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=_GENERATION_SYSTEM_PROMPT,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )
    return (response.text or "").strip()


def knowledge_agent(state: PakAssistState) -> PakAssistState:
    """Entry point — wire this in as the real "knowledge" node in graph.py."""
    query = state.get("user_input", "").strip()
    if not query:
        state["response"] = NO_CONTEXT_MESSAGE
        state["sources"] = []
        return state

    retriever = _get_retriever()

    uploaded_files = state.get("uploaded_files") or []
    if uploaded_files:
        retriever.add_user_content(_extract_uploaded_files(uploaded_files))

    chunks = retriever.retrieve(query)

    if not chunks:
        state["response"] = NO_CONTEXT_MESSAGE
        state["sources"] = []
        return state

    context_block = _build_context_block(chunks)
    answer = _call_gemini(query, context_block)

    state["response"] = answer or NO_CONTEXT_MESSAGE
    state["sources"] = _chunks_to_source_refs(chunks)
    return state
