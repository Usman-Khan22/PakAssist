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
import re
from pathlib import Path
from typing import List

from backend.graph.state import PakAssistState, SourceRef
from backend.rag.loader import RagDocument
from backend.rag.multimodal import extract_text_from_image, extract_text_from_pdf
from backend.rag.retriever import Retriever, RetrievedChunk
from backend.services.checklist_builder import (
    CHECKLIST_SYSTEM_PROMPT,
    checklist_retrieval_query,
    is_checklist_request,
    select_requirement_chunks,
)
from backend.services.fee_lookup import (
    FEE_SYSTEM_PROMPT,
    fee_retrieval_query,
    is_fee_request,
    select_fee_chunks,
)
from backend.services.journey import update_journey
from backend.services.language import generation_instruction, message
from backend.services.verification import (
    verify_document_answer,
    verify_fee_sources,
    verify_journey_transition,
    verify_requirement_sources,
)

NO_CONTEXT_MESSAGE = (
    "I couldn't find reliable information for this request in the current "
    "knowledge base."
)
UPLOAD_SESSION_MESSAGE = (
    "I couldn't access the uploaded content because this request has no valid "
    "session context."
)
UPLOAD_REQUIRED_MESSAGE = (
    "Please upload or provide the document you want me to inspect."
)

_UPLOAD_MARKERS = ("upload", "uploaded")
_UPLOAD_CONTENT_NOUNS = (
    "image",
    "document",
    "file",
    "pdf",
    "photo",
    "screenshot",
    "notice",
    "form",
    "letter",
)
_UPLOAD_INSPECTION_TERMS = (
    "visible",
    "inspect",
    "read",
    "explain",
    "summarize",
    "summarise",
    "identify",
    "extract",
    "describe",
    "tell me",
    "what does",
    "what is in",
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


def _call_gemini(
    query: str, context_block: str, system_prompt: str = _GENERATION_SYSTEM_PROMPT
) -> str:
    from google.genai import types

    client = _get_client()
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    prompt = f"Retrieved context:\n{context_block}\n\nCitizen's question:\n{query}"

    # No `tools=`, AFC explicitly disabled — same fix as the Planner.
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )
    return (response.text or "").strip()


def is_upload_inspection_request(query: str) -> bool:
    """Identify requests to interpret user-provided image/document content."""
    text = query.casefold()
    has_upload_reference = any(
        re.search(rf"\b{re.escape(term)}\b", text)
        for term in (*_UPLOAD_MARKERS, *_UPLOAD_CONTENT_NOUNS)
    )
    return has_upload_reference and any(
        re.search(rf"\b{re.escape(term)}\b", text)
        for term in _UPLOAD_INSPECTION_TERMS
    )


def knowledge_agent(
    state: PakAssistState, *, thread_id: str | None = None
) -> PakAssistState:
    """Entry point — wire this in as the real "knowledge" node in graph.py."""
    query = state.get("user_input", "").strip()
    if not query:
        state["response"] = NO_CONTEXT_MESSAGE
        state["sources"] = []
        return state

    uploaded_files = state.get("uploaded_files") or []
    upload_inspection = is_upload_inspection_request(query)
    if (uploaded_files or upload_inspection) and (
        not isinstance(thread_id, str) or not thread_id.strip()
    ):
        state["response"] = UPLOAD_SESSION_MESSAGE
        state["sources"] = []
        return state

    retriever = _get_retriever()

    if uploaded_files:
        retriever.add_user_content(
            _extract_uploaded_files(uploaded_files), thread_id=thread_id
        )

    intent = state.get("intent", "")
    service_type = state.get("service_type", "")
    preferred_language = state.get("preferred_language", "english")
    simple_language = bool(state.get("simple_language"))
    document_mode = intent in {
        "inspect_upload",
        "simple_document_explanation",
        "document_presentation",
    }
    checklist_mode = not document_mode and is_checklist_request(intent, query)
    fee_mode = not document_mode and is_fee_request(intent, query)

    retrieval_query = query
    top_k = None
    if checklist_mode:
        retrieval_query = checklist_retrieval_query(service_type, query)
        top_k = 20
    elif fee_mode:
        retrieval_query = fee_retrieval_query(service_type, query)
        top_k = 20
    elif intent in {"simple_explanation", "language_rerender"} and state.get(
        "response"
    ):
        retrieval_query = (
            f"{service_type.replace('_', ' ')} {state['response']} {query}"
        )

    trusted_mode = checklist_mode or fee_mode
    chunks = retriever.retrieve(
        retrieval_query,
        top_k=top_k,
        include_user_files=not trusted_mode,
        thread_id=thread_id,
        prefer_user_files=(
            not trusted_mode
            and (bool(uploaded_files) or upload_inspection or document_mode)
        ),
    )

    if document_mode:
        chunks = [chunk for chunk in chunks if chunk.origin == "user_upload"]

    if not chunks:
        state["response"] = (
            message("upload_required", preferred_language)
            if document_mode
            else message("no_context", preferred_language)
        )
        state["sources"] = []
        return state

    system_prompt = _GENERATION_SYSTEM_PROMPT
    source_chunks = chunks

    if checklist_mode:
        source_chunks = select_requirement_chunks(chunks, service_type)
        if not verify_requirement_sources(source_chunks, service_type):
            state["response"] = message("checklist_not_found", preferred_language)
            state["sources"] = []
            return state
        system_prompt = CHECKLIST_SYSTEM_PROMPT
    elif fee_mode:
        matching_fee_chunks, reliable_fee_chunks = select_fee_chunks(
            chunks, service_type
        )
        if not verify_fee_sources(reliable_fee_chunks, service_type):
            state["response"] = message("fee_not_found", preferred_language)
            state["sources"] = _chunks_to_source_refs(matching_fee_chunks)
            return state
        source_chunks = reliable_fee_chunks
        system_prompt = FEE_SYSTEM_PROMPT

    if preferred_language != "english" or simple_language:
        system_prompt += "\n\nPresentation:\n" + generation_instruction(
            preferred_language, simple=simple_language
        )

    context_block = _build_context_block(source_chunks)
    answer = _call_gemini(query, context_block, system_prompt=system_prompt)

    if document_mode and answer and not verify_document_answer(answer, source_chunks):
        state["response"] = message("verification_failed", preferred_language)
        state["sources"] = _chunks_to_source_refs(source_chunks)
        return state

    state["response"] = answer or message("no_context", preferred_language)
    state["sources"] = _chunks_to_source_refs(source_chunks)
    if answer and checklist_mode and verify_journey_transition(
        "requirements", "reviewed", True
    ):
        state["journeys"] = update_journey(state, "requirements", "reviewed")
    elif answer and fee_mode and verify_journey_transition("fees", "reviewed", True):
        state["journeys"] = update_journey(state, "fees", "reviewed")
    return state
