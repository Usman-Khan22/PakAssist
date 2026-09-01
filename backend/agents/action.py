"""Action Agent and supported-action dispatch."""

from __future__ import annotations

from typing import Any

from backend.graph.state import PakAssistState, SourceRef
from backend.services.service_centers import (
    ServiceCenterLookupResult,
    lookup_service_centers,
)


_LOOKUP_TERMS = ("center", "centre", "office", "where", "nearest", "location")


def _requested_action(state: PakAssistState) -> str | None:
    intent = state.get("intent", "").casefold()
    query = state.get("user_input", "").casefold()
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


def action_agent(state: PakAssistState) -> dict:
    """Dispatch the action requested by the Planner to a supported action."""
    action = _requested_action(state)
    if action != "service_center_lookup":
        return {
            "response": "This action is not supported yet. I can currently look up service centers.",
            "sources": [],
        }

    result = lookup_service_centers(
        state.get("service_type", "unknown"), state.get("user_input", "")
    )
    return {"response": _lookup_response(result), "sources": _source_refs(result)}

