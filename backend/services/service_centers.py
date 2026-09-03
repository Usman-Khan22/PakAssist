"""Dataset-backed service-center lookup."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal


_DATA_DIR = Path(__file__).resolve().parents[2] / "knowledge_base"
_DATASET_FILES = {
    "passport": "passport_service_centers.json",
    "driving_license": "driving_license_service_centers.json",
}
_LOCATION_PATTERN = re.compile(
    r"\b(?:in|near|at|around)\s+([a-z][a-z .'-]*?)(?=[?.!,;]|$)", re.IGNORECASE
)
_ROMAN_URDU_LOCATION_PATTERN = re.compile(
    r"\b([a-z][a-z .'-]*?)\s+mein\b", re.IGNORECASE
)
_LOCATION_STOP_WORDS = {
    "a",
    "an",
    "center",
    "centre",
    "driving",
    "find",
    "license",
    "licence",
    "office",
    "passport",
    "service",
    "the",
}
_URDU_LOCATION_ALIASES = {
    "کراچی": "Karachi",
    "لاہور": "Lahore",
    "اسلام آباد": "Islamabad",
    "راولپنڈی": "Rawalpindi",
    "اٹک": "Attock",
    "پشاور": "Peshawar",
    "کوئٹہ": "Quetta",
    "ملتان": "Multan",
    "فیصل آباد": "Faisalabad",
}


@dataclass(frozen=True)
class ServiceCenterLookupResult:
    status: Literal["found", "missing_location", "no_results", "unsupported_service"]
    service_type: str
    location: str | None
    centers: list[dict[str, Any]]


def _normalize(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


@lru_cache(maxsize=None)
def _load_centers(service_type: str) -> tuple[dict[str, Any], ...]:
    filename = _DATASET_FILES[service_type]
    with (_DATA_DIR / filename).open(encoding="utf-8") as dataset:
        records = json.load(dataset)
    if not isinstance(records, list):
        raise ValueError(f"Service-center dataset must contain a JSON list: {filename}")
    return tuple(records)


def _record_text(record: dict[str, Any]) -> str:
    fields = (
        record.get("region"),
        record.get("province"),
        record.get("office_name"),
        record.get("address"),
    )
    return _normalize(" ".join(str(value) for value in fields if value))


def _extract_location(query: str, records: tuple[dict[str, Any], ...]) -> str | None:
    for urdu_name, dataset_name in _URDU_LOCATION_ALIASES.items():
        if urdu_name in query:
            return dataset_name

    roman_match = _ROMAN_URDU_LOCATION_PATTERN.search(query)
    if roman_match:
        candidate = roman_match.group(1).strip()
        words = [
            word
            for word in candidate.split()
            if word.casefold() not in _LOCATION_STOP_WORDS
        ]
        if words:
            return " ".join(words)

    match = _LOCATION_PATTERN.search(query)
    if match:
        candidate = match.group(1).strip()
        words = [word for word in candidate.split() if word.casefold() not in _LOCATION_STOP_WORDS]
        if words:
            return " ".join(words)

    normalized_query = _normalize(query)
    known_locations: set[str] = set()
    for record in records:
        for field in ("region", "province", "office_name"):
            value = record.get(field)
            if value:
                known_locations.add(str(value))

    for location in sorted(known_locations, key=len, reverse=True):
        if _normalize(location) in normalized_query:
            return location
    return None


def lookup_service_centers(
    service_type: str, query: str, *, limit: int = 5
) -> ServiceCenterLookupResult:
    """Find centers matching an explicit location or office name in ``query``."""
    if service_type not in _DATASET_FILES:
        return ServiceCenterLookupResult(
            status="unsupported_service",
            service_type=service_type,
            location=None,
            centers=[],
        )

    records = _load_centers(service_type)
    location = _extract_location(query, records)
    if not location:
        return ServiceCenterLookupResult(
            status="missing_location",
            service_type=service_type,
            location=None,
            centers=[],
        )

    normalized_location = _normalize(location)
    matches = [record for record in records if normalized_location in _record_text(record)]
    return ServiceCenterLookupResult(
        status="found" if matches else "no_results",
        service_type=service_type,
        location=location,
        centers=matches[:limit],
    )
