"""
Simple chat service for configuration management.

This is a simplified version that manages configuration reloading
without the complex agent architecture from the original app.
"""

import logging
from typing import Any, Dict, Optional

from src.core.settings_db import get_settings, load_settings_from_database

logger = logging.getLogger(__name__)


class ChatService:
    """
    Simplified chat service for configuration management.

    This service handles hot-reloading of configuration from the database.
    In the template, there's no global agent to reload - configuration is
    loaded per-request from the database via get_settings().

    This class exists mainly for backward compatibility with the profiles API.
    """

    def __init__(self):
        """Initialize chat service."""
        self.current_profile_id: Optional[int] = None
        logger.info("ChatService initialized")

    def reload_agent(self, profile_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Reload configuration from database.

        In the simplified template architecture, there's no global agent state to reload.
        Configuration is fetched per-request from the database via get_settings().

        This method exists for API compatibility but doesn't actually reload anything.
        The next request will automatically use the updated configuration from the database.

        Args:
            profile_id: Optional profile ID to load (None = use default)

        Returns:
            Dictionary with reload status and profile information
        """
        try:
            # Load settings to verify profile exists and get profile info
            if profile_id:
                settings = load_settings_from_database(profile_id)
                self.current_profile_id = profile_id
            else:
                settings = get_settings()
                self.current_profile_id = settings.profile_id

            logger.info(
                f"Configuration reloaded for profile {settings.profile_id}: {settings.profile_name}"
            )

            return {
                "status": "success",
                "message": "Configuration reloaded successfully",
                "profile_id": settings.profile_id,
                "profile_name": settings.profile_name,
                "note": "In the template architecture, configuration is loaded per-request from the database. "
                        "Changes to profile settings will be reflected in the next request automatically.",
            }

        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}", exc_info=True)
            raise ValueError(f"Failed to reload configuration: {str(e)}")


# Global chat service instance (singleton pattern)
_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """
    Get or create the global chat service instance.

    Returns:
        ChatService instance
    """
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
