"""Session and message models for persistent session storage.

These models support multi-session functionality in production deployments
where session state is stored in Lakebase for persistence across app restarts.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from src.core.database import Base


class ChatRequest(Base):
    """Tracks async chat requests for polling.

    Used by the polling-based streaming implementation to track request
    status and results when SSE is not available (e.g., Databricks Apps).
    """

    __tablename__ = "chat_requests"

    id = Column(Integer, primary_key=True)
    request_id = Column(String(64), unique=True, nullable=False, index=True)
    session_id = Column(
        Integer,
        ForeignKey("user_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(String(20), default="pending")  # pending/running/completed/error
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Final result data (JSON) - stores response data for async polling
    result_json = Column(Text, nullable=True)

    # Relationship
    session = relationship("UserSession")

    __table_args__ = (Index("ix_chat_requests_session_id", "session_id"),)

    def __repr__(self):
        return f"<ChatRequest(request_id='{self.request_id}', status='{self.status}')>"


class UserSession(Base):
    """User session for tracking conversation state.

    Each session represents an independent conversation context with its own
    chat history and application state.
    """

    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)  # Optional user identification

    # Session metadata
    title = Column(String(255))  # Optional session title/name
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Processing lock for concurrent request handling
    is_processing = Column(Boolean, default=False, nullable=False)
    processing_started_at = Column(DateTime, nullable=True)

    # Relationships
    messages = relationship(
        "SessionMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SessionMessage.created_at",
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_user_sessions_user_last_activity", "user_id", "last_activity"),
    )

    def __repr__(self):
        return f"<UserSession(session_id='{self.session_id}', user_id='{self.user_id}')>"


class SessionMessage(Base):
    """Chat message within a session.

    Stores the conversation history for replay and context.
    """

    __tablename__ = "session_messages"

    id = Column(Integer, primary_key=True)
    session_id = Column(
        Integer,
        ForeignKey("user_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Message content
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Optional metadata
    message_type = Column(String(50))  # 'chat', 'tool_call', 'tool_result', 'error', etc.
    metadata_json = Column(Text)  # JSON string for additional metadata

    # Async polling support - links messages to specific chat requests
    request_id = Column(String(64), nullable=True, index=True)

    # Relationship
    session = relationship("UserSession", back_populates="messages")

    def __repr__(self):
        return f"<SessionMessage(id={self.id}, role='{self.role}', session_id={self.session_id})>"



