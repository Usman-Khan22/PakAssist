"""
PakAssist shared graph state.

Field names here match the real repo's contract as described in
PROJECT_CONTEXT.md: `user_input`, `intent`, `service_type`, `next_step`,
`response` already exist and are initialized in main.py / filled by the
Planner and the terminal nodes. This RAG milestone adds exactly one new
field: `sources`, needed for Trusted Source Visibility. The Knowledge Agent
writes its answer into the existing `response` field — it does not need a
new one.

Do not replace the real state.py with this file — merge only the new
`sources` field (and the `uploaded_files` field, if you want multimodal
input support this milestone) into it.
"""

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
    # existing fields (main.py / Planner)
    user_input: str
    intent: str
    service_type: str
    next_step: str
    response: str

    # optional: user-provided files for this turn (paths on disk).
    # Only needed if you're wiring in multimodal input this milestone —
    # drop this field if uploads aren't part of the current scope.
    uploaded_files: List[str]

    # new field required by the Knowledge Agent (Trusted Source Visibility)
    sources: Optional[List[SourceRef]]
