"""Simple environment-based application settings.

This module provides settings loaded from environment variables with sensible defaults.
No database required for configuration - just set environment variables.

Environment Variables:
    LLM_ENDPOINT: Model serving endpoint name (default: databricks-claude-sonnet-4-5)
    LLM_TEMPERATURE: Sampling temperature 0.0-2.0 (default: 0.7)
    LLM_MAX_TOKENS: Maximum response tokens (default: 2048)
    SYSTEM_PROMPT: System prompt for the AI (default: helpful assistant)
"""

import os
import logging
from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Default system prompt
DEFAULT_SYSTEM_PROMPT = """You are a helpful AI assistant powered by Databricks. You provide clear,
accurate, and concise responses to user questions.

Format your responses using markdown for better readability:
- Use **bold** for emphasis
- Use bullet points for lists
- Use code blocks for code snippets
- Use headings to organize longer responses

Be friendly, professional, and helpful."""


class LLMSettings(BaseSettings):
    """LLM configuration settings from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        extra="allow"
    )

    endpoint: str = Field(
        default="databricks-claude-sonnet-4-5",
        description="Databricks model serving endpoint name"
    )
    temperature: float = Field(
        default=0.7,
        description="Sampling temperature (0.0-2.0)"
    )
    max_tokens: int = Field(
        default=2048,
        description="Maximum tokens in response"
    )

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v

    @field_validator("max_tokens")
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        if v < 1 or v > 64000:
            raise ValueError("max_tokens must be between 1 and 64000")
        return v


class PromptsSettings(BaseSettings):
    """Prompts configuration from environment variables."""

    model_config = SettingsConfigDict(extra="allow")

    system_prompt: str = Field(
        default=DEFAULT_SYSTEM_PROMPT,
        description="System prompt defining AI behavior"
    )


class AppSettings(BaseSettings):
    """Main application settings from environment variables.
    
    Simple configuration that works out-of-the-box with sensible defaults.
    Override via environment variables as needed.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )

    # LLM settings
    llm: LLMSettings = Field(default_factory=LLMSettings)
    
    # Prompts settings
    prompts: PromptsSettings = Field(default_factory=PromptsSettings)

    # Environment identifier
    environment: str = Field(
        default="development",
        description="Environment name (development, staging, production)"
    )


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Get the application settings singleton.
    
    Settings are loaded from environment variables with sensible defaults.
    No database required.
    
    Returns:
        Cached AppSettings instance
    """
    settings = AppSettings()
    logger.info(
        "Settings loaded from environment",
        extra={
            "llm_endpoint": settings.llm.endpoint,
            "llm_temperature": settings.llm.temperature,
            "llm_max_tokens": settings.llm.max_tokens,
            "environment": settings.environment,
        }
    )
    return settings


def reload_settings() -> AppSettings:
    """Reload settings from environment.
    
    Clears the cache and loads fresh settings.
    
    Returns:
        New AppSettings instance
    """
    get_settings.cache_clear()
    return get_settings()

