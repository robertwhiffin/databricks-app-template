"""Core configuration and infrastructure.

This module provides the core infrastructure for the Databricks Chat App Template:
- Database connection management (PostgreSQL/Lakebase)
- Databricks client singleton
- Environment-based settings management
"""

from src.core.database import get_db, get_db_session, init_db
from src.core.databricks_client import (
    DatabricksClientError,
    get_databricks_client,
    reset_client,
    verify_connection,
)
from src.core.settings import AppSettings, get_settings, reload_settings

__all__ = [
    # Database
    "get_db",
    "get_db_session",
    "init_db",
    # Databricks client
    "DatabricksClientError",
    "get_databricks_client",
    "reset_client",
    "verify_connection",
    # Settings
    "AppSettings",
    "get_settings",
    "reload_settings",
]
