from typing import List, Optional, TypedDict


class SourceRef(TypedDict):
    """One attributable source shown to the user (Trusted Source Visibility)."""

    label: str  # e.g. "Driving License Guide" or "Uploaded document"
    origin: str  # "knowledge_base" | "user_upload"
    service: Optional[str]
    section: Optional[str]
    source_url: Optional[str]
    confidence: Optional[str]


class PakAssistState(TypedDict, total=False):
    user_input: str
    intent: str
    service_type: str
    next_step: str
    response: str
    uploaded_files: Optional[List[str]]
    sources: Optional[List[SourceRef]]