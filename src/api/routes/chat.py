"""Chat API endpoints."""
import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from src.api.schemas.chat import ChatRequest, ChatResponse, Message
from src.api.services.session_manager import SessionManager
from src.services.chat_model import ChatModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])

# Initialize services
session_manager = SessionManager()
chat_model = ChatModel()


@router.post("/chat", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Send a chat message and get a response.

    This endpoint:
    1. Creates or retrieves a session
    2. Loads conversation history
    3. Calls the model serving endpoint
    4. Saves the response
    5. Returns the full conversation

    Args:
        request: Chat request with message and optional session_id

    Returns:
        ChatResponse with session_id, messages, and assistant response
    """
    try:
        # Get or create session
        if request.session_id:
            session_id = request.session_id
            # Verify session exists
            try:
                session_manager.get_session(session_id)
            except Exception:
                # Session doesn't exist, create it
                session = session_manager.create_session(user_id="default_user")
                session_id = session["session_id"]
        else:
            # Create new session
            session = session_manager.create_session(user_id="default_user")
            session_id = session["session_id"]

        # Get conversation history
        history = session_manager.get_messages(session_id)
        conversation_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history
        ]

        # Add user message to history
        session_manager.add_message(
            session_id=session_id,
            role="user",
            content=request.message
        )

        # Format messages for model
        messages = chat_model.format_conversation_context(
            conversation_history=conversation_history,
            new_user_message=request.message
        )

        # Call model
        response_text = await chat_model.generate(messages)

        # Save assistant response
        session_manager.add_message(
            session_id=session_id,
            role="assistant",
            content=response_text
        )

        # Get updated message history
        updated_history = session_manager.get_messages(session_id)
        messages_list = [
            Message(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg.get("created_at")
            )
            for msg in updated_history
        ]

        return ChatResponse(
            session_id=session_id,
            messages=messages_list,
            response=response_text
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "databricks-chat-template"
    }
