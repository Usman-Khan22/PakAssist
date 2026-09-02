from typing import Dict, List, Optional, TypedDict


class SourceRef(TypedDict):
    """One attributable source shown to the user (Trusted Source Visibility)."""

    label: str  # e.g. "Driving License Guide" or "Uploaded document"
    origin: str  # "knowledge_base" | "user_upload"
    service: Optional[str]
    section: Optional[str]
    source_url: Optional[str]
    confidence: Optional[str]


class JourneyProgress(TypedDict, total=False):
    requirements: str
    fees: str
    service_center: str
    appointment: str


class PakAssistState(TypedDict, total=False):
    user_input: str
    intent: str
    service_type: str
    next_step: str
    response: str
    uploaded_files: Optional[List[str]]
    sources: Optional[List[SourceRef]]
    pending_clarification: Optional[str]
    pending_request: Optional[str]
    office_options: Optional[List[str]]
    selected_office: Optional[str]
    appointment_date: Optional[str]
    booked_slots: Optional[List[str]]
    journeys: Dict[str, JourneyProgress]
