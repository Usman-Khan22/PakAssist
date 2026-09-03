"""Session-local tracking for PakAssist assistance journeys."""

from __future__ import annotations

from typing import Literal

from backend.graph.state import JourneyProgress, PakAssistState


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
    return (
        f"I can guide you through the {service} process, including required "
        "documents, trusted fee information, service centers, and demo appointment "
        "booking. A good place to start is the required documents. Would you like "
        "to see them?"
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
    if service in {"", "unknown"}:
        return "Which government service should I show progress for?"

    progress = (state.get("journeys") or {}).get(service, {})
    labels = {
        "requirements": {
            "reviewed": "✓ Requirements reviewed",
            None: "○ Requirements not reviewed yet",
        },
        "fees": {
            "reviewed": "✓ Fee information reviewed",
            None: "○ Fee information not reviewed yet",
        },
        "service_center": {
            "located": "✓ Service centers located",
            "selected": "✓ Service center selected",
            None: "○ Service center not located yet",
        },
        "appointment": {
            "availability_checked": "◐ Demo appointment availability checked; not booked",
            "demo_booked": "✓ Demo appointment booked",
            None: "○ Demo appointment not booked yet",
        },
    }
    lines = [f"{service.replace('_', ' ').title()} assistance journey"]
    for step in ("requirements", "fees", "service_center", "appointment"):
        status = progress.get(step)
        lines.append(labels[step].get(status, labels[step][None]))
    lines.append(
        "This tracks assistance provided by PakAssist, not verified government completion."
    )
    return "\n".join(lines)
