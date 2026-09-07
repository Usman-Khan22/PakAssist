"""Action Agent and supported-action dispatch."""

from __future__ import annotations

import re
from typing import Any

from backend.graph.state import PakAssistState, SourceRef
from backend.services.appointment_simulator import (
    AppointmentResult,
    book_slot,
    check_slots,
)
from backend.services.journey import is_journey_request, journey_summary, update_journey
from backend.services.language import message
from backend.services.service_centers import (
    ServiceCenterLookupResult,
    lookup_service_centers,
)
from backend.services.verification import (
    verify_booking_confirmation,
    verify_journey_transition,
)


_LOOKUP_TERMS = ("center", "centre", "office", "where", "nearest", "location")
_ORDINALS = {
    "first": 0,
    "1st": 0,
    "second": 1,
    "2nd": 1,
    "third": 2,
    "3rd": 2,
    "fourth": 3,
    "4th": 3,
    "fifth": 4,
    "5th": 4,
    "sixth": 5,
    "6th": 5,
    "seventh": 6,
    "7th": 6,
    "eighth": 7,
    "8th": 7,
    "ninth": 8,
    "9th": 8,
    "tenth": 9,
    "10th": 9,
    "pehla": 0,
    "pehli": 0,
    "pehle": 0,
    "doosra": 1,
    "doosri": 1,
    "doosre": 1,
}


def _requested_action(state: PakAssistState) -> str | None:
    intent = state.get("intent", "").casefold()
    query = state.get("user_input", "").casefold()
    if is_journey_request(intent, query):
        return "journey_summary"
    if intent == "book_slot":
        return "book_slot"
    if intent == "check_slots":
        return "check_slots"
    if "book" in query and ("slot" in query or "appointment" in query):
        return "book_slot"
    if "appointment" in query or "available slot" in query:
        return "check_slots"
    if "center" in intent or "centre" in intent or "office" in intent or "location" in intent:
        return "service_center_lookup"
    if any(term in query for term in _LOOKUP_TERMS):
        return "service_center_lookup"
    return None


def _format_center(center: dict[str, Any], number: int, language: str) -> str:
    lines = [f"{number}. {center['office_name']}"]
    labels = {
        "english": {
            "Address": "Address", "Phone": "Phone", "Service": "Service",
            "Services": "Services", "Hours": "Hours", "Portal": "Portal",
            "Confidence": "Confidence", "Source": "Source",
        },
        "roman_urdu": {
            "Address": "Pata", "Phone": "Phone", "Service": "Service",
            "Services": "Services", "Hours": "Auqaat", "Portal": "Portal",
            "Confidence": "Bharosa", "Source": "Source",
        },
        "urdu": {
            "Address": "پتہ", "Phone": "فون", "Service": "سروس",
            "Services": "سروسز", "Hours": "اوقات", "Portal": "پورٹل",
            "Confidence": "اعتماد", "Source": "ماخذ",
        },
    }.get(language, {})
    for label, key in (
        ("Address", "address"),
        ("Phone", "phone"),
        ("Service", "service"),
        ("Services", "services"),
        ("Hours", "hours"),
        ("Portal", "portal"),
        ("Confidence", "confidence"),
        ("Source", "source"),
    ):
        value = center.get(key)
        if value:
            if isinstance(value, list):
                value = ", ".join(str(item) for item in value)
            lines.append(f"   {labels.get(label, label)}: {value}")
    return "\n".join(lines)


def _source_refs(result: ServiceCenterLookupResult) -> list[SourceRef]:
    refs: list[SourceRef] = []
    seen: set[str] = set()
    for center in result.centers:
        source = center.get("source") or center.get("portal")
        if not source or source in seen:
            continue
        seen.add(source)
        refs.append(
            SourceRef(
                label=center["office_name"],
                origin="knowledge_base",
                service=result.service_type,
                section="service_centers",
                source_url=source,
                confidence=center.get("confidence"),
            )
        )
    return refs


def _lookup_response(result: ServiceCenterLookupResult, language: str) -> str:
    service_label = result.service_type.replace("_", " ")
    if result.status == "missing_location":
        return message("lookup_missing_location", language, service=service_label)
    if result.status == "no_results":
        return message(
            "lookup_no_results",
            language,
            service=service_label,
            location=result.location,
        )
    if result.status == "unsupported_service":
        return message("lookup_unsupported", language, service=service_label)

    heading = message(
        "lookup_found", language, service=service_label, location=result.location
    )
    details = "\n\n".join(
        _format_center(center, number, language)
        for number, center in enumerate(result.centers, start=1)
    )
    return f"{heading}\n\n{details}"


def _normalize(value: str) -> str:
    return " ".join(value.casefold().replace("-", " ").split())


def _resolve_office_reference(
    state: PakAssistState,
) -> tuple[str | None, bool]:
    query = _normalize(state.get("user_input", ""))
    options = state.get("office_options") or []

    numeric_match = re.fullmatch(r"\d+", query) or re.search(
        r"\b(?:for|office|option|number)\s+(?:the\s+)?(\d+)\b", query
    )
    if numeric_match:
        raw_number = (
            numeric_match.group(0) if query.isdigit() else numeric_match.group(1)
        )
        index = int(raw_number) - 1
        return (options[index], False) if 0 <= index < len(options) else (None, True)

    for ordinal, index in _ORDINALS.items():
        if re.search(rf"\b{re.escape(ordinal)}\b", query):
            return (options[index], False) if index < len(options) else (None, True)

    for office in options:
        normalized_office = _normalize(office)
        if normalized_office in query or query in normalized_office:
            return office, False

    selected = state.get("selected_office")
    if selected:
        return selected, False
    if len(options) == 1:
        return options[0], False
    return None, False


def _office_selection_response(options: list[str], language: str) -> str:
    choices = "\n".join(
        f"{number}. {office}" for number, office in enumerate(options, start=1)
    )
    return message("office_selection", language) + "\n" + choices


def _invalid_office_reference_response(options: list[str], language: str) -> str:
    count = len(options)
    return message("invalid_office", language, count=count)


def _find_appointment_office(state: PakAssistState) -> tuple[str | None, dict | None]:
    language = state.get("preferred_language", "english")
    current_lookup = lookup_service_centers(
        state.get("service_type", "unknown"), state.get("user_input", "")
    )
    if current_lookup.status in {"found", "no_results"}:
        if current_lookup.status == "no_results":
            return None, {
                "response": _lookup_response(current_lookup, language),
                "sources": [],
                "pending_clarification": None,
                "pending_request": None,
                "office_options": [],
                "selected_office": None,
                "appointment_date": None,
            }

        current_options = [center["office_name"] for center in current_lookup.centers]
        if len(current_options) > 1:
            return None, {
                "response": _office_selection_response(current_options, language),
                "sources": [],
                "pending_clarification": "office",
                "pending_request": state.get("user_input"),
                "office_options": current_options,
                "selected_office": None,
                "appointment_date": None,
            }
        return current_options[0], None

    office, invalid_reference = _resolve_office_reference(state)
    if invalid_reference:
        options = state.get("office_options") or []
        return None, {
            "response": _invalid_office_reference_response(options, language),
            "sources": [],
            "pending_clarification": "office",
            "pending_request": state.get("user_input"),
        }
    if office:
        return office, None

    existing_options = state.get("office_options") or []
    if len(existing_options) > 1:
        return None, {
            "response": _office_selection_response(existing_options, language),
            "sources": [],
            "pending_clarification": "office",
            "pending_request": state.get("user_input"),
        }

    result = current_lookup
    if result.status == "missing_location":
        return None, {
            "response": _lookup_response(result, language),
            "sources": [],
            "pending_clarification": "location",
            "pending_request": state.get("user_input"),
            "office_options": [],
            "selected_office": None,
        }
    if result.status != "found":
        return None, {
            "response": _lookup_response(result, language),
            "sources": [],
            "pending_clarification": None,
            "pending_request": None,
            "office_options": [],
            "selected_office": None,
        }

    options = [center["office_name"] for center in result.centers]
    if len(options) > 1:
        return None, {
            "response": _office_selection_response(options, language),
            "sources": [],
            "pending_clarification": "office",
            "pending_request": state.get("user_input"),
            "office_options": options,
            "selected_office": None,
        }
    return options[0], None


def _availability_response(result: AppointmentResult, language: str) -> str:
    if result.status == "not_configured":
        return message(
            "availability_not_configured", language, office=result.office_name
        )
    if not result.slots:
        return message(
            "availability_empty",
            language,
            office=result.office_name,
            date=result.date,
        )
    return message(
        "availability",
        language,
        office=result.office_name,
        date=result.date,
        slots=", ".join(result.slots),
    )


def _booking_response(
    result: AppointmentResult, language: str, *, verified: bool = True
) -> str:
    if result.status == "booked":
        if not verified:
            return message("booking_verification_failed", language)
        return message(
            "booking_confirmed",
            language,
            office=result.office_name,
            date=result.date,
            time=result.requested_time,
            reference=result.booking_reference,
        )
    if result.status == "missing_time":
        return message("booking_missing_time", language)
    if result.status == "slot_not_found":
        return message(
            "booking_slot_not_found",
            language,
            time=result.requested_time,
            office=result.office_name,
            date=result.date,
        )
    if result.status == "unavailable":
        return message(
            "booking_unavailable",
            language,
            time=result.requested_time,
            office=result.office_name,
        )
    return message(
        "availability_not_configured", language, office=result.office_name
    )


def _run_service_center_lookup(state: PakAssistState) -> dict:
    language = state.get("preferred_language", "english")
    result = lookup_service_centers(
        state.get("service_type", "unknown"), state.get("user_input", "")
    )
    pending_location = result.status == "missing_location"
    options = [center["office_name"] for center in result.centers]
    update = {
        "response": _lookup_response(result, language),
        "sources": _source_refs(result),
        "pending_clarification": "location" if pending_location else None,
        "pending_request": state.get("user_input") if pending_location else None,
        "office_options": options,
        "selected_office": options[0] if len(options) == 1 else None,
        "appointment_date": None,
    }
    if result.status == "found":
        status = "selected" if len(options) == 1 else "located"
        if verify_journey_transition("service_center", status, True):
            update["journeys"] = update_journey(state, "service_center", status)
    return update


def _run_check_slots(state: PakAssistState) -> dict:
    language = state.get("preferred_language", "english")
    office, clarification = _find_appointment_office(state)
    if clarification:
        return clarification

    result = check_slots(
        state.get("service_type", "unknown"),
        office,
        state.get("booked_slots"),
    )
    update = {
        "response": _availability_response(result, language),
        "sources": [],
        "pending_clarification": None,
        "pending_request": None,
        "selected_office": office,
        "appointment_date": result.date,
    }
    if result.status == "available" and verify_journey_transition(
        "appointment", "availability_checked", True
    ):
        journeys = update_journey(state, "service_center", "selected")
        progress_state = {**state, "journeys": journeys}
        update["journeys"] = update_journey(
            progress_state, "appointment", "availability_checked"
        )
    return update


def _run_book_slot(state: PakAssistState) -> dict:
    language = state.get("preferred_language", "english")
    office, clarification = _find_appointment_office(state)
    if clarification:
        return clarification

    available_before = check_slots(
        state.get("service_type", "unknown"),
        office,
        state.get("booked_slots"),
    )
    result = book_slot(
        state.get("service_type", "unknown"),
        office,
        state.get("user_input", ""),
        state.get("booked_slots"),
    )
    booked_slots = list(state.get("booked_slots") or [])
    if result.booked_slot_key:
        booked_slots.append(result.booked_slot_key)
    booking_verified = result.status != "booked" or verify_booking_confirmation(
        result, available_before, booked_slots
    )
    if result.status == "booked" and not booking_verified:
        booked_slots = list(state.get("booked_slots") or [])
    update = {
        "response": _booking_response(result, language, verified=booking_verified),
        "sources": [],
        "pending_clarification": None,
        "pending_request": None,
        "selected_office": office,
        "appointment_date": result.date,
        "booked_slots": booked_slots,
    }
    if result.status == "booked" and booking_verified and verify_journey_transition(
        "appointment", "demo_booked", True
    ):
        journeys = update_journey(state, "service_center", "selected")
        progress_state = {**state, "journeys": journeys}
        update["journeys"] = update_journey(
            progress_state, "appointment", "demo_booked"
        )
    return update


def action_agent(state: PakAssistState) -> dict:
    """Dispatch the action requested by the Planner to a supported action."""
    action = _requested_action(state)
    if action == "service_center_lookup":
        return _run_service_center_lookup(state)
    if action == "check_slots":
        return _run_check_slots(state)
    if action == "book_slot":
        return _run_book_slot(state)
    if action == "journey_summary":
        return {
            "response": journey_summary(state),
            "sources": [],
            "pending_clarification": None,
            "pending_request": None,
        }
    return {
        "response": message(
            "unsupported_action", state.get("preferred_language", "english")
        ),
        "sources": [],
        "pending_clarification": None,
        "pending_request": None,
    }
