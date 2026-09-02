"""Action Agent and supported-action dispatch."""

from __future__ import annotations

from typing import Any

from backend.graph.state import PakAssistState, SourceRef
from backend.services.appointment_simulator import (
    AppointmentResult,
    book_slot,
    check_slots,
)
from backend.services.service_centers import (
    ServiceCenterLookupResult,
    lookup_service_centers,
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
}


def _requested_action(state: PakAssistState) -> str | None:
    intent = state.get("intent", "").casefold()
    query = state.get("user_input", "").casefold()
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


def _format_center(center: dict[str, Any], number: int) -> str:
    lines = [f"{number}. {center['office_name']}"]
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
            lines.append(f"   {label}: {value}")
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


def _lookup_response(result: ServiceCenterLookupResult) -> str:
    service_label = result.service_type.replace("_", " ")
    if result.status == "missing_location":
        return f"Which city or region should I search for a {service_label} service center in?"
    if result.status == "no_results":
        return (
            f"I couldn't find a {service_label} service center for {result.location} "
            "in the current dataset."
        )
    if result.status == "unsupported_service":
        return f"Service-center lookup is not available for {service_label}."

    heading = f"I found these {service_label} service centers for {result.location}:"
    details = "\n\n".join(
        _format_center(center, number)
        for number, center in enumerate(result.centers, start=1)
    )
    return f"{heading}\n\n{details}"


def _normalize(value: str) -> str:
    return " ".join(value.casefold().replace("-", " ").split())


def _resolve_office_reference(state: PakAssistState) -> str | None:
    query = _normalize(state.get("user_input", ""))
    options = state.get("office_options") or []

    if query.isdigit():
        index = int(query) - 1
        if 0 <= index < len(options):
            return options[index]

    for ordinal, index in _ORDINALS.items():
        if ordinal in query and index < len(options):
            return options[index]

    for office in options:
        normalized_office = _normalize(office)
        if normalized_office in query or query in normalized_office:
            return office

    selected = state.get("selected_office")
    if selected:
        return selected
    if len(options) == 1:
        return options[0]
    return None


def _office_selection_response(options: list[str]) -> str:
    choices = "\n".join(
        f"{number}. {office}" for number, office in enumerate(options, start=1)
    )
    return (
        "Several matching offices are available. Which office should I use for "
        "the demo appointment? Reply with its name or number:\n" + choices
    )


def _find_appointment_office(state: PakAssistState) -> tuple[str | None, dict | None]:
    office = _resolve_office_reference(state)
    if office:
        return office, None

    existing_options = state.get("office_options") or []
    if len(existing_options) > 1:
        return None, {
            "response": _office_selection_response(existing_options),
            "sources": [],
            "pending_clarification": "office",
            "pending_request": state.get("user_input"),
        }

    result = lookup_service_centers(
        state.get("service_type", "unknown"), state.get("user_input", "")
    )
    if result.status == "missing_location":
        return None, {
            "response": _lookup_response(result),
            "sources": [],
            "pending_clarification": "location",
            "pending_request": state.get("user_input"),
            "office_options": [],
            "selected_office": None,
        }
    if result.status != "found":
        return None, {
            "response": _lookup_response(result),
            "sources": [],
            "pending_clarification": None,
            "pending_request": None,
            "office_options": [],
            "selected_office": None,
        }

    options = [center["office_name"] for center in result.centers]
    if len(options) > 1:
        return None, {
            "response": _office_selection_response(options),
            "sources": [],
            "pending_clarification": "office",
            "pending_request": state.get("user_input"),
            "office_options": options,
            "selected_office": None,
        }
    return options[0], None


def _availability_response(result: AppointmentResult) -> str:
    if result.status == "not_configured":
        return (
            f"No demo appointment schedule is configured for {result.office_name}. "
            "This does not reflect real government availability."
        )
    if not result.slots:
        return (
            f"No simulated slots remain for {result.office_name} on {result.date}. "
            "Check the official government booking system for real availability."
        )
    return (
        "Simulated prototype availability — not live government availability.\n"
        f"Office: {result.office_name}\n"
        f"Date: {result.date}\n"
        f"Available demo slots: {', '.join(result.slots)}\n"
        "A real appointment must be checked through the official government system."
    )


def _booking_response(result: AppointmentResult) -> str:
    if result.status == "booked":
        return (
            "Simulated booking confirmed (demo only).\n"
            f"Office: {result.office_name}\n"
            f"Date: {result.date}\n"
            f"Time: {result.requested_time}\n"
            f"Demo reference: {result.booking_reference}\n"
            "No real government appointment was created; use the official booking "
            "system for an actual appointment."
        )
    if result.status == "missing_time":
        return "Which demo appointment time would you like to book?"
    if result.status == "slot_not_found":
        return (
            f"The {result.requested_time} demo slot does not exist for "
            f"{result.office_name} on {result.date}."
        )
    if result.status == "unavailable":
        return (
            f"The {result.requested_time} demo slot for {result.office_name} is "
            "already unavailable or booked in this simulation."
        )
    return (
        f"No demo appointment schedule is configured for {result.office_name}. "
        "This does not reflect real government availability."
    )


def _run_service_center_lookup(state: PakAssistState) -> dict:
    result = lookup_service_centers(
        state.get("service_type", "unknown"), state.get("user_input", "")
    )
    pending_location = result.status == "missing_location"
    options = [center["office_name"] for center in result.centers]
    return {
        "response": _lookup_response(result),
        "sources": _source_refs(result),
        "pending_clarification": "location" if pending_location else None,
        "pending_request": state.get("user_input") if pending_location else None,
        "office_options": options,
        "selected_office": options[0] if len(options) == 1 else None,
        "appointment_date": None,
    }


def _run_check_slots(state: PakAssistState) -> dict:
    office, clarification = _find_appointment_office(state)
    if clarification:
        return clarification

    result = check_slots(
        state.get("service_type", "unknown"),
        office,
        state.get("booked_slots"),
    )
    return {
        "response": _availability_response(result),
        "sources": [],
        "pending_clarification": None,
        "pending_request": None,
        "selected_office": office,
        "appointment_date": result.date,
    }


def _run_book_slot(state: PakAssistState) -> dict:
    office, clarification = _find_appointment_office(state)
    if clarification:
        return clarification

    result = book_slot(
        state.get("service_type", "unknown"),
        office,
        state.get("user_input", ""),
        state.get("booked_slots"),
    )
    booked_slots = list(state.get("booked_slots") or [])
    if result.booked_slot_key:
        booked_slots.append(result.booked_slot_key)
    return {
        "response": _booking_response(result),
        "sources": [],
        "pending_clarification": None,
        "pending_request": None,
        "selected_office": office,
        "appointment_date": result.date,
        "booked_slots": booked_slots,
    }


def action_agent(state: PakAssistState) -> dict:
    """Dispatch the action requested by the Planner to a supported action."""
    action = _requested_action(state)
    if action == "service_center_lookup":
        return _run_service_center_lookup(state)
    if action == "check_slots":
        return _run_check_slots(state)
    if action == "book_slot":
        return _run_book_slot(state)
    return {
        "response": (
            "This action is not supported yet. I can look up service centers "
            "and simulate appointment slots."
        ),
        "sources": [],
        "pending_clarification": None,
        "pending_request": None,
    }
