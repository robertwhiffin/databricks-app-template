"""Chat API schemas."""
from typing import List, Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    """A chat message."""

    role: str = Field(..., description="Message role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="ISO timestamp")


class ChatRequest(BaseModel):
    """Request to send a chat message."""

    message: str = Field(..., description="User's message", min_length=1)
    session_id: Optional[str] = Field(None, description="Session ID (auto-created if not provided)")


class ChatResponse(BaseModel):
    """Response from chat endpoint."""

    session_id: str = Field(..., description="Session ID")
    messages: List[Message] = Field(..., description="Conversation messages")
    response: str = Field(..., description="Assistant's response")
