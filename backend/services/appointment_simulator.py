"""Deterministic, in-memory-per-session appointment simulation."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal


_SLOT_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "appointment_slots.json"


@dataclass(frozen=True)
class AppointmentResult:
    status: Literal[
        "available",
        "booked",
        "not_configured",
        "missing_time",
        "slot_not_found",
        "unavailable",
    ]
    office_name: str
    date: str | None = None
    slots: tuple[str, ...] = ()
    requested_time: str | None = None
    booking_reference: str | None = None
    booked_slot_key: str | None = None


@lru_cache(maxsize=1)
def _load_schedules() -> tuple[dict, ...]:
    with _SLOT_DATA_PATH.open(encoding="utf-8") as source:
        schedules = json.load(source)
    if not isinstance(schedules, list):
        raise ValueError("Appointment simulator data must contain a JSON list.")
    return tuple(schedules)


def _find_schedule(service_type: str, office_name: str) -> dict | None:
    for schedule in _load_schedules():
        if (
            schedule.get("service_type") == service_type
            and schedule.get("office_name") == office_name
        ):
            return schedule
    return None


def _slot_key(service_type: str, office_name: str, date: str, time: str) -> str:
    return "|".join((service_type, office_name, date, time))


def normalize_requested_time(query: str) -> str | None:
    """Extract a 24-hour HH:MM time from common user phrasing."""
    match = re.search(
        r"\b([01]?\d|2[0-3])(?::([0-5]\d))?\s*(a\.?m\.?|p\.?m\.?)?\b",
        query,
        re.IGNORECASE,
    )
    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    meridiem = (match.group(3) or "").casefold().replace(".", "")
    if meridiem == "pm" and hour < 12:
        hour += 12
    elif meridiem == "am" and hour == 12:
        hour = 0
    return f"{hour:02d}:{minute:02d}"


def check_slots(
    service_type: str, office_name: str, booked_slots: list[str] | None = None
) -> AppointmentResult:
    schedule = _find_schedule(service_type, office_name)
    if schedule is None:
        return AppointmentResult(status="not_configured", office_name=office_name)

    booked = set(booked_slots or [])
    date = schedule["date"]
    available = tuple(
        time
        for time in schedule["slots"]
        if _slot_key(service_type, office_name, date, time) not in booked
    )
    return AppointmentResult(
        status="available",
        office_name=office_name,
        date=date,
        slots=available,
    )


def book_slot(
    service_type: str,
    office_name: str,
    query: str,
    booked_slots: list[str] | None = None,
) -> AppointmentResult:
    schedule = _find_schedule(service_type, office_name)
    if schedule is None:
        return AppointmentResult(status="not_configured", office_name=office_name)

    requested_time = normalize_requested_time(query)
    date = schedule["date"]
    if requested_time is None:
        return AppointmentResult(
            status="missing_time", office_name=office_name, date=date
        )
    if requested_time not in schedule["slots"]:
        return AppointmentResult(
            status="slot_not_found",
            office_name=office_name,
            date=date,
            requested_time=requested_time,
        )

    key = _slot_key(service_type, office_name, date, requested_time)
    if key in set(booked_slots or []):
        return AppointmentResult(
            status="unavailable",
            office_name=office_name,
            date=date,
            requested_time=requested_time,
        )

    reference = "DEMO-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:8].upper()
    return AppointmentResult(
        status="booked",
        office_name=office_name,
        date=date,
        requested_time=requested_time,
        booking_reference=reference,
        booked_slot_key=key,
    )

