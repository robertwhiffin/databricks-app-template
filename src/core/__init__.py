"""Core configuration and infrastructure.

This module provides the core infrastructure for the Databricks Chat App Template:
- Database connection management (PostgreSQL/Lakebase)
- Databricks client singleton
- Database-backed settings management

Note: This template uses database-backed configuration (settings_db.py) rather than
file-based config loading. YAML files in config/ only seed the initial database state.
"""

from src.core.database import get_db, get_db_session, init_db
from src.core.databricks_client import (
    DatabricksClientError,
    get_databricks_client,
    reset_client,
    verify_connection,
)
from src.core.settings_db import AppSettings, get_settings, load_settings_from_database, reload_settings

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
    "load_settings_from_database",
    "reload_settings",
]

