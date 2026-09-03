"""Session-local tracking for PakAssist assistance journeys."""

from __future__ import annotations

from typing import Literal

from backend.graph.state import JourneyProgress, PakAssistState
from backend.services.language import message


JourneyStep = Literal["requirements", "fees", "service_center", "appointment"]

_SERVICE_JOURNEY_INTENTS = {
    "apply_for_service",
    "renew_service",
    "service_journey",
    "start_service_journey",
}

_SUMMARY_PHRASES = (
    "my progress",
    "show progress",
    "journey progress",
    "what have we done",
    "what have we completed",
    "what's left",
    "what is left",
)


def is_journey_request(intent: str, query: str) -> bool:
    normalized_intent = intent.casefold()
    normalized_query = query.casefold()
    return normalized_intent in {"journey_summary", "progress_summary"} or any(
        phrase in normalized_query for phrase in _SUMMARY_PHRASES
    )


def is_service_journey_goal(intent: str) -> bool:
    return intent.casefold() in _SERVICE_JOURNEY_INTENTS


def initialize_journey(state: PakAssistState) -> dict[str, JourneyProgress]:
    """Create an empty service journey without advancing assistance progress."""
    service = state.get("service_type")
    journeys = {
        name: dict(progress) for name, progress in (state.get("journeys") or {}).items()
    }
    if service not in {None, "", "unknown"}:
        journeys.setdefault(service, {})
    return journeys


def journey_orientation(state: PakAssistState) -> str:
    service = state.get("service_type", "service").replace("_", " ")
    return message(
        "journey_orientation",
        state.get("preferred_language", "english"),
        service=service,
    )


def update_journey(
    state: PakAssistState,
    step: JourneyStep,
    status: str,
    *,
    service_type: str | None = None,
) -> dict[str, JourneyProgress]:
    """Return a copied journey mapping with one service-specific update."""
    service = service_type or state.get("service_type")
    journeys = {
        name: dict(progress) for name, progress in (state.get("journeys") or {}).items()
    }
    if service in {None, "", "unknown"}:
        return journeys
    progress = dict(journeys.get(service, {}))
    progress[step] = status
    journeys[service] = progress
    return journeys


def journey_summary(state: PakAssistState) -> str:
    service = state.get("service_type", "unknown")
    language = state.get("preferred_language", "english")
    if service in {"", "unknown"}:
        return message("journey_service_needed", language)

    progress = (state.get("journeys") or {}).get(service, {})
    labels = {
        "requirements": {
            "reviewed": message("journey_requirements_done", language),
            None: message("journey_requirements_pending", language),
        },
        "fees": {
            "reviewed": message("journey_fees_done", language),
            None: message("journey_fees_pending", language),
        },
        "service_center": {
            "located": message("journey_center_located", language),
            "selected": message("journey_center_selected", language),
            None: message("journey_center_pending", language),
        },
        "appointment": {
            "availability_checked": message("journey_slots_checked", language),
            "demo_booked": message("journey_booking_done", language),
            None: message("journey_booking_pending", language),
        },
    }
    lines = [
        message(
            "journey_title", language, service=service.replace("_", " ").title()
        )
    ]
    for step in ("requirements", "fees", "service_center", "appointment"):
        status = progress.get(step)
        lines.append(labels[step].get(status, labels[step][None]))
    lines.append(message("journey_disclaimer", language))
    return "\n".join(lines)
