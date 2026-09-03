from typing import List, Optional

from pydantic import BaseModel, Field


class SessionResponse(BaseModel):
    session_id: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


class SourceResponse(BaseModel):
    label: str
    origin: str
    service: Optional[str] = None
    section: Optional[str] = None
    source_url: Optional[str] = None
    confidence: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    response: str
    sources: List[SourceResponse] = Field(default_factory=list)