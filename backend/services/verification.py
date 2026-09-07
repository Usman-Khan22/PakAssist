"""Selective deterministic verification for high-value response paths."""

from __future__ import annotations

import re

from backend.rag.retriever import RetrievedChunk
from backend.services.appointment_simulator import AppointmentResult


def verify_requirement_sources(
    chunks: list[RetrievedChunk], service_type: str
) -> bool:
    return bool(chunks) and all(
        chunk.origin == "knowledge_base"
        and chunk.metadata.get("service") == service_type
        and "required document"
        in str(chunk.metadata.get("section", "")).casefold()
        for chunk in chunks
    )


def verify_fee_sources(chunks: list[RetrievedChunk], service_type: str) -> bool:
    return bool(chunks) and all(
        chunk.origin == "knowledge_base"
        and chunk.metadata.get("service") == service_type
        and "fee" in str(chunk.metadata.get("section", "")).casefold()
        and str(chunk.metadata.get("confidence", "")).casefold() == "high"
        and "unverified" not in chunk.text.casefold()
        for chunk in chunks
    )


def verify_document_sources(chunks: list[RetrievedChunk]) -> bool:
    return bool(chunks) and all(chunk.origin == "user_upload" for chunk in chunks)


_CRITICAL_LITERAL_RE = re.compile(
    r"\b(?:\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?|\d+(?:[.,]\d+)?|"
    r"\d{1,2}\s+(?:january|february|march|april|may|june|july|august|"
    r"september|october|november|december))\b",
    re.IGNORECASE,
)
_ACTION_TERMS = (
    "apply",
    "bring",
    "call",
    "collect",
    "contact",
    "email",
    "online",
    "pay",
    "portal",
    "send",
    "submit",
    "visit",
)


def verify_document_answer(answer: str, chunks: list[RetrievedChunk]) -> bool:
    """Require upload grounding and reject unsupported dates/numeric claims."""
    if not answer.strip() or not verify_document_sources(chunks):
        return False
    context = "\n".join(chunk.text for chunk in chunks).casefold()
    normalized_answer = answer.casefold()
    literals = {match.casefold() for match in _CRITICAL_LITERAL_RE.findall(answer)}
    if not all(literal in context for literal in literals):
        return False
    answer_actions = {term for term in _ACTION_TERMS if term in normalized_answer}
    return all(term in context for term in answer_actions)


def verify_booking_confirmation(
    result: AppointmentResult,
    available_before: AppointmentResult,
    recorded_slots: list[str],
) -> bool:
    return bool(
        result.status == "booked"
        and available_before.status == "available"
        and result.requested_time in available_before.slots
        and result.office_name == available_before.office_name
        and result.date == available_before.date
        and result.booking_reference
        and result.booked_slot_key
        and result.booked_slot_key in recorded_slots
    )


def verify_journey_transition(step: str, status: str, succeeded: bool) -> bool:
    allowed = {
        ("requirements", "reviewed"),
        ("fees", "reviewed"),
        ("service_center", "located"),
        ("service_center", "selected"),
        ("appointment", "availability_checked"),
        ("appointment", "demo_booked"),
    }
    return succeeded and (step, status) in allowed
