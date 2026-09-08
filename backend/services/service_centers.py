"""Dataset-backed service-center lookup."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal


_DATA_DIR = Path(__file__).resolve().parents[2] / "knowledge_base"
_DATASET_FILES = {
    "passport": "passport_service_centers.json",
    "driving_license": "driving_license_service_centers (1).json",
}
_LOCATION_PATTERN = re.compile(
    r"\b(?:in|near|at|around)\s+([a-z][a-z .'-]*?)(?=\s+(?:mein|main|me)\b|[?.!,;]|$)", re.IGNORECASE
)
_ROMAN_URDU_LOCATION_PATTERN = re.compile(
    r"\b([a-z][a-z .'-]*?)\s+(?:mein|main|me)\b", re.IGNORECASE
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
    "offices",
    "passport",
    "passports",
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
    missing_locations: list[str] = field(default_factory=list)


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

    match = _LOCATION_PATTERN.search(query)
    if match:
        candidate = match.group(1).strip()
        words = [word for word in candidate.split() if word.casefold() not in _LOCATION_STOP_WORDS]
        if words:
            return " ".join(words)

    for roman_match in _ROMAN_URDU_LOCATION_PATTERN.finditer(query):
        candidate = roman_match.group(1).strip()
        words = [
            word
            for word in candidate.split()
            if word.casefold() not in _LOCATION_STOP_WORDS
        ]
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


def _extract_locations(query: str, records: tuple[dict[str, Any], ...]) -> list[str]:
    """Split explicit city lists without silently dropping unknown locations."""
    explicit = re.search(r"\b(?:in|near|at|around)\s+(.+)$", query, re.IGNORECASE)
    if not explicit:
        location = _extract_location(query, records)
        return [location] if location else []
    candidate = explicit.group(1).strip(" .!?؟۔")
    # 'near me Karachi' supplies a city after the conversational 'me'.
    candidate = re.sub(r"^me\s+", "", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"\s+(?:me|mein|main)$", "", candidate, flags=re.IGNORECASE)
    names = set(_URDU_LOCATION_ALIASES.values())
    names.update(str(record[key]) for record in records for key in ("region", "city") if record.get(key))
    alternatives = "|".join(re.escape(name) for name in sorted(names, key=len, reverse=True))
    city = re.compile(rf"(?:{alternatives})", re.IGNORECASE)
    locations = []
    for part in re.split(r"\s*(?:[,،;&]|\band\b|\baur\b|\bor\b|اور)\s*", candidate, flags=re.IGNORECASE):
        part = part.strip()
        if not part:
            continue
        # Also accept lists without commas: 'Islamabad Lahore and Karachi'.
        matches = list(city.finditer(part))
        remainder = city.sub("", part).strip()
        pieces = [match.group() for match in matches] if matches and not remainder else [part]
        for piece in pieces:
            if piece.casefold() not in {value.casefold() for value in locations}:
                locations.append(piece)
    return locations


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
    # Resolve an explicit dataset office before interpreting the entire suffix
    # after 'in' as a city. Preserve any separately specified city constraint.
    named_records = [
        record for record in records
        if re.search(rf"(?<!\w){re.escape(str(record['office_name']))}(?!\w)", query, re.IGNORECASE)
    ]
    if named_records:
        location_query = query
        for record in named_records:
            location_query = re.sub(re.escape(str(record["office_name"])), "", location_query, flags=re.IGNORECASE)
        location_query = re.sub(
            r"\bfor\s+(?:(?:passport|driving licen[cs]e)\s+)?(?:office\s*)?(?=$|[.!?])",
            "", location_query, flags=re.IGNORECASE,
        ).strip()
        locations = _extract_locations(location_query, records) if re.search(
            r"\b(?:in|near|at|around)\s+", location_query, re.IGNORECASE
        ) else []
        matches = [record for record in named_records if not locations or any(
            _normalize(location) in _record_text(record) for location in locations
        )]
        return ServiceCenterLookupResult(
            status="found" if matches else "no_results",
            service_type=service_type,
            location=", ".join(locations) if locations else ", ".join(str(record["office_name"]) for record in named_records),
            centers=matches,
        )
    locations = _extract_locations(query, records)
    if not locations:
        return ServiceCenterLookupResult(
            status="missing_location",
            service_type=service_type,
            location=None,
            centers=[],
        )

    matches = []
    missing_locations = []
    for location in locations:
        normalized_location = _normalize(location)
        city_matches = [record for record in records if normalized_location in _record_text(record)][:limit]
        if not city_matches:
            missing_locations.append(location)
        for record in city_matches:
            if record not in matches:
                matches.append(record)
    return ServiceCenterLookupResult(
        status="found" if matches else "no_results",
        service_type=service_type,
        location=", ".join(locations),
        centers=matches,
        missing_locations=missing_locations,
    )
