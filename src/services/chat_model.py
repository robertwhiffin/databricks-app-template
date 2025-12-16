"""Direct Databricks model serving integration without LangChain.

⚠️ THIS IS THE MAIN FILE YOU'LL CUSTOMIZE FOR YOUR USE CASE ⚠️

This module provides a simple wrapper around Databricks model serving endpoints.
It replaces complex LangChain agents with straightforward API calls that you can
easily understand and modify.

💡 CUSTOMIZATION TIP:
   - Want to add RAG? Modify the generate() method to include retrieved context
   - Want function calling? Add tool handling in generate()
   - Want to change the model? Set the LLM_ENDPOINT environment variable

📚 WHAT THIS FILE DOES:
   1. Wraps Databricks model serving endpoint calls
   2. Formats conversation history for the model
   3. Handles streaming responses
   4. Manages errors gracefully

🔗 RELATED FILES:
   - src/core/settings.py - Environment-based configuration
   - src/api/routes/chat.py - API endpoint that uses this class

Environment Variables:
   - LLM_ENDPOINT: Model serving endpoint name (default: databricks-meta-llama-3-1-70b-instruct)
   - LLM_TEMPERATURE: Sampling temperature 0.0-2.0 (default: 0.7)
   - LLM_MAX_TOKENS: Maximum response tokens (default: 2048)
   - SYSTEM_PROMPT: System prompt for the AI
"""
from typing import AsyncGenerator, Dict, List, Optional
import asyncio

from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
from src.core.databricks_client import get_databricks_client
from src.core.settings import get_settings


class ChatModel:
    """Simple chat model wrapper for Databricks model serving endpoints.

    This class provides a clean interface for calling Databricks model serving
    endpoints without the complexity of LangChain. It handles:
    - Message formatting
    - Streaming responses
    - Conversation context
    - Error handling

    Example usage:
        ```python
        chat_model = ChatModel()
        messages = [
            {"role": "user", "content": "Hello, how are you?"}
        ]
        response = await chat_model.generate(messages)
        print(response)  # "I'm doing well, thank you for asking!"
        ```
    """

    def __init__(self):
        """Initialize the chat model with settings from environment.

        Settings are loaded from environment variables with sensible defaults.
        No database or YAML files needed for configuration.

        What happens here:
        1. get_settings() loads settings from environment variables
        2. get_databricks_client() returns a singleton WorkspaceClient
        3. Settings include: model endpoint, temperature, max_tokens, prompts
        """
        # Load settings from environment variables
        self.settings = get_settings()

        # Get singleton Databricks client (reused across requests for efficiency)
        self.client = get_databricks_client()

    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
    ) -> str:
        """Generate a response from the model.

        🎯 THIS IS THE CORE METHOD YOU'LL CUSTOMIZE 🎯

        This method is called every time a user sends a message. It:
        1. Prepares the request payload
        2. Calls the Databricks model serving endpoint
        3. Extracts and returns the response

        💡 CUSTOMIZATION EXAMPLES:

        Add RAG (Retrieval-Augmented Generation):
            # Before calling the model, retrieve relevant documents
            user_query = messages[-1]["content"]
            docs = await retrieve_documents(user_query)
            messages.insert(1, {"role": "system", "content": f"Context: {docs}"})

        Add function calling:
            # Check if model wants to call a function
            response = await self._call_endpoint(payload)
            if "function_call" in response:
                result = await execute_function(response["function_call"])
                # Continue conversation with function result

        Add validation:
            # Validate user input before calling model
            if contains_profanity(messages[-1]["content"]):
                return "I cannot respond to that type of content."

        Args:
            messages: List of message dicts with 'role' and 'content' keys
                     Role must be 'user', 'assistant', or 'system'
                     Example: [{"role": "user", "content": "Hello!"}]
            max_tokens: Maximum tokens in response (uses setting default if None)
            temperature: Sampling temperature 0.0-1.0 (uses setting default if None)
            stream: Whether to stream the response (not yet implemented)

        Returns:
            The generated response text as a string

        Raises:
            Exception: If the model serving endpoint returns an error
        """
        # STEP 1: Use settings defaults if parameters not provided
        # These come from environment variables (see src/core/settings.py)
        max_tokens = max_tokens or self.settings.llm.max_tokens
        temperature = temperature or self.settings.llm.temperature

        # STEP 2: Prepare the request payload for the model serving endpoint
        # ⚠️ IMPORTANT: Different model endpoints may require different formats!
        #
        # This template uses the OpenAI-compatible format (works with most endpoints):
        # - Foundation Model APIs (Llama, Mistral, etc.)
        # - OpenAI-compatible custom endpoints
        # - Anthropic Claude (with slight modifications)
        #
        # 💡 TIP: If your endpoint uses a different format, modify this section
        payload = {
            "messages": messages,  # List of {"role": "...", "content": "..."} dicts
            "max_tokens": max_tokens,  # Maximum response length
            "temperature": temperature,  # Randomness (0.0 = deterministic, 1.0 = creative)
        }

        # STEP 3: Call the model serving endpoint
        # We use asyncio.to_thread to make the synchronous SDK call non-blocking
        # This prevents the async server from getting stuck waiting for the model
        try:
            response = await asyncio.to_thread(
                self._call_endpoint,
                payload
            )

            # STEP 4: Extract the response text from the endpoint response
            # ⚠️ WARNING: Different endpoints return different response formats!
            # You may need to modify this section based on your endpoint.

            if isinstance(response, dict):
                # FORMAT 1: OpenAI-compatible (most common)
                # Example: {"choices": [{"message": {"content": "Hello!"}}]}
                if "choices" in response:
                    return response["choices"][0]["message"]["content"]

                # FORMAT 2: Anthropic Claude format
                # Example: {"candidates": [{"text": "Hello!"}]}
                elif "candidates" in response:
                    return response["candidates"][0]["text"]

                # FORMAT 3: Simple text response
                # Example: {"text": "Hello!"}
                elif "text" in response:
                    return response["text"]

                # FORMAT 4: Unknown format - raise error with helpful message
                else:
                    raise ValueError(
                        f"Unexpected response format from model endpoint. "
                        f"Response: {response}. "
                        f"💡 TIP: Check your endpoint documentation and update "
                        f"this method in src/services/chat_model.py to handle the format."
                    )
            else:
                # Simple string response (rare, but possible)
                return str(response)

        except Exception as e:
            # Provide helpful error message
            raise Exception(
                f"Error calling model serving endpoint '{self.settings.llm.endpoint}': {e}\n\n"
                f"💡 TROUBLESHOOTING:\n"
                f"1. Verify the endpoint exists: Check Databricks UI > Serving\n"
                f"2. Verify endpoint is running: Status should be 'Ready'\n"
                f"3. Check endpoint name: LLM_ENDPOINT env var (current: {self.settings.llm.endpoint})\n"
                f"4. Test endpoint manually: Use Databricks UI to send a test request"
            )

    def _call_endpoint(self, payload: Dict) -> Dict:
        """Call the Databricks model serving endpoint synchronously.

        ⚠️ IMPORTANT: This method runs in a thread pool (called via asyncio.to_thread)
        to avoid blocking the async event loop.

        DO NOT call this method directly - use generate() instead!

        What this does:
        1. Looks up the endpoint name from database settings
        2. Calls the Databricks SDK's serving_endpoints.query() method
        3. Returns the response as a dictionary

        Args:
            payload: Request payload (messages, max_tokens, temperature)

        Returns:
            Response dictionary from the model endpoint

        Raises:
            Exception: If endpoint doesn't exist, is stopped, or returns an error
        """
        # Convert dict messages to SDK ChatMessage objects
        # The SDK expects ChatMessage objects, not plain dicts
        messages_list = payload.pop('messages', [])
        sdk_messages = [
            ChatMessage(
                role=ChatMessageRole(msg['role']),
                content=msg['content']
            )
            for msg in messages_list
        ]

        # Call the Databricks model serving endpoint using the SDK
        # The endpoint name comes from the LLM_ENDPOINT environment variable
        # Default: databricks-meta-llama-3-1-70b-instruct
        response = self.client.serving_endpoints.query(
            name=self.settings.llm.endpoint,  # e.g., "databricks-meta-llama-3-1-70b-instruct"
            messages=sdk_messages,
            **payload  # Remaining parameters: max_tokens, temperature, etc.
        )

        # Response is already a dict, no need to call as_dict()
        if hasattr(response, 'as_dict'):
            return response.as_dict()
        return response

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the model.

        This method yields response chunks as they arrive, enabling
        real-time streaming to the frontend.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Yields:
            Response chunks as they arrive

        Note:
            Streaming support depends on the model serving endpoint.
            Some endpoints may not support streaming.
        """
        # Use settings defaults if not provided
        max_tokens = max_tokens or self.settings.llm.max_tokens
        temperature = temperature or self.settings.llm.temperature

        # Prepare the request payload with streaming enabled
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,  # Enable streaming
        }

        try:
            # TODO: Implement actual streaming with Databricks SDK
            # For now, we'll do a simple non-streaming call and yield it all at once
            # Real streaming would use: client.serving_endpoints.query_stream()

            response_text = await self.generate(messages, max_tokens, temperature, stream=False)

            # Simulate streaming by yielding in chunks
            # In production, you'd yield actual chunks from the streaming API
            chunk_size = 20  # Characters per chunk
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i + chunk_size]
                yield chunk
                # Small delay to simulate streaming
                await asyncio.sleep(0.05)

        except Exception as e:
            yield f"Error: {e}"

    def format_system_prompt(self) -> Dict[str, str]:
        """Get the system prompt from settings as a formatted message.

        The system prompt defines the AI's personality and behavior.
        It comes from the SYSTEM_PROMPT environment variable (or default).

        💡 TO CUSTOMIZE THE AI'S BEHAVIOR:
        Set the SYSTEM_PROMPT environment variable, or modify the default
        in src/core/settings.py

        Example system prompts:
        - Customer support: "You are a helpful customer support agent..."
        - Code assistant: "You are an expert programmer who writes clean code..."
        - Data analyst: "You are a data analyst who explains insights clearly..."

        Returns:
            A message dict with role='system' and the system prompt content
            Example: {"role": "system", "content": "You are a helpful assistant..."}
        """
        return {
            "role": "system",
            "content": self.settings.prompts.system_prompt
        }

    def format_conversation_context(
        self,
        conversation_history: List[Dict[str, str]],
        new_user_message: str
    ) -> List[Dict[str, str]]:
        """Format conversation context for the model.

        This method combines the system prompt, conversation history,
        and new user message into a properly formatted messages list that
        the model can understand.

        💡 CONVERSATION FLOW:
        1. System prompt (defines AI behavior) - ALWAYS FIRST
        2. Previous messages (provides context) - user and assistant messages alternating
        3. New user message (what to respond to) - ALWAYS LAST

        Example output:
        [
            {"role": "system", "content": "You are a helpful assistant..."},
            {"role": "user", "content": "What's the weather?"},
            {"role": "assistant", "content": "I don't have real-time weather data..."},
            {"role": "user", "content": "How do I check it?"}  # <- new message
        ]

        ⚠️ WARNING: The order matters! System prompt must be first, new message must be last.

        Args:
            conversation_history: Previous messages in the conversation (excluding new message)
                                 List of {"role": "user/assistant", "content": "..."}
            new_user_message: The new message from the user (string)

        Returns:
            Complete messages list ready to send to the model
        """
        messages = []

        # STEP 1: Add system prompt (defines AI personality/behavior)
        # This is ALWAYS first and sets the context for the conversation
        messages.append(self.format_system_prompt())

        # STEP 2: Add conversation history (provides context from previous turns)
        # This maintains conversation continuity so the AI remembers what was discussed
        messages.extend(conversation_history)

        # STEP 3: Add new user message (what the AI should respond to)
        # This is ALWAYS last - it's the message we're asking the AI to respond to
        messages.append({
            "role": "user",
            "content": new_user_message
        })

        return messages


# ============================================================================
# CONVENIENCE FUNCTION - Quick helper for simple use cases
# ============================================================================

async def chat(user_message: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
    """Quick helper function for simple chat interactions without sessions.

    ⚠️ NOTE: This function does NOT use sessions or save history to database!
    It's useful for testing or one-off queries, but for production use cases,
    use the full ChatModel class with SessionManager instead.

    💡 USE THIS FOR:
    - Quick testing: response = await chat("Hello!")
    - One-off queries: answer = await chat("What is 2+2?")
    - Prototyping: Testing prompts without full app setup

    💡 DON'T USE THIS FOR:
    - Production chat apps (use ChatModel + SessionManager instead)
    - Multi-turn conversations that need persistence
    - User-facing features (sessions provide better user experience)

    Args:
        user_message: The user's message (string)
        conversation_history: Optional list of previous messages
                             Format: [{"role": "user/assistant", "content": "..."}]

    Returns:
        The model's response as a string

    Example:
        ```python
        # Simple query (no history)
        response = await chat("What is the capital of France?")
        print(response)  # "The capital of France is Paris."

        # With conversation history
        history = [
            {"role": "user", "content": "Hi, I'm learning French"},
            {"role": "assistant", "content": "That's great! How can I help?"}
        ]
        response = await chat("What's the capital?", history)
        print(response)  # "The capital of France is Paris."
        ```
    """
    # Create a new ChatModel instance (loads settings from environment)
    model = ChatModel()

    # Use empty list if no history provided
    history = conversation_history or []

    # Format messages (adds system prompt, history, and new message)
    messages = model.format_conversation_context(history, user_message)

    # Generate and return response
    return await model.generate(messages)
