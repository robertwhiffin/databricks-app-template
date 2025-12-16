"""Session API schemas."""
from typing import List, Optional
from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    """Request to create a new session."""

    user_id: Optional[str] = None
    title: Optional[str] = None


class SessionInfo(BaseModel):
    """Session information."""

    session_id: str
    user_id: Optional[str] = None
    title: Optional[str] = None
    created_at: str
    last_activity: str
    message_count: int


class SessionListResponse(BaseModel):
    """List of sessions."""

    sessions: List[SessionInfo]
