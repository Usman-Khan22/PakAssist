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


def _office_selection_response(options: list[str]) -> str:
    choices = "\n".join(
        f"{number}. {office}" for number, office in enumerate(options, start=1)
    )
    return (
        "Several matching offices are available. Which office should I use for "
        "the demo appointment? Reply with its name or number:\n" + choices
    )


def _invalid_office_reference_response(options: list[str]) -> str:
    count = len(options)
    return (
        f"There are only {count} matching offices. "
        f"Please choose an office from 1 to {count}."
    )


def _find_appointment_office(state: PakAssistState) -> tuple[str | None, dict | None]:
    current_lookup = lookup_service_centers(
        state.get("service_type", "unknown"), state.get("user_input", "")
    )
    if current_lookup.status in {"found", "no_results"}:
        if current_lookup.status == "no_results":
            return None, {
                "response": _lookup_response(current_lookup),
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
                "response": _office_selection_response(current_options),
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
            "response": _invalid_office_reference_response(options),
            "sources": [],
            "pending_clarification": "office",
            "pending_request": state.get("user_input"),
        }
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

    result = current_lookup
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
    update = {
        "response": _lookup_response(result),
        "sources": _source_refs(result),
        "pending_clarification": "location" if pending_location else None,
        "pending_request": state.get("user_input") if pending_location else None,
        "office_options": options,
        "selected_office": options[0] if len(options) == 1 else None,
        "appointment_date": None,
    }
    if result.status == "found":
        status = "selected" if len(options) == 1 else "located"
        update["journeys"] = update_journey(state, "service_center", status)
    return update


def _run_check_slots(state: PakAssistState) -> dict:
    office, clarification = _find_appointment_office(state)
    if clarification:
        return clarification

    result = check_slots(
        state.get("service_type", "unknown"),
        office,
        state.get("booked_slots"),
    )
    update = {
        "response": _availability_response(result),
        "sources": [],
        "pending_clarification": None,
        "pending_request": None,
        "selected_office": office,
        "appointment_date": result.date,
    }
    journeys = update_journey(state, "service_center", "selected")
    update["journeys"] = journeys
    if result.status == "available":
        progress_state = {**state, "journeys": journeys}
        update["journeys"] = update_journey(
            progress_state, "appointment", "availability_checked"
        )
    return update


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
    update = {
        "response": _booking_response(result),
        "sources": [],
        "pending_clarification": None,
        "pending_request": None,
        "selected_office": office,
        "appointment_date": result.date,
        "booked_slots": booked_slots,
    }
    if result.status == "booked":
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
        "response": (
            "This action is not supported yet. I can look up service centers "
            "and simulate appointment slots."
        ),
        "sources": [],
        "pending_clarification": None,
        "pending_request": None,
    }
