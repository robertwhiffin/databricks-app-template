"""
Logging configuration for the application.

This module sets up structured logging based on environment variables.

Environment Variables:
    LOG_LEVEL: Logging level (default: INFO)
    LOG_FORMAT: Logging format - 'json' or 'text' (default: json)
"""

import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # Add any extra fields passed to the logger
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
                "request_id",
            ]:
                log_data[key] = value

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter."""

    def __init__(self):
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def setup_logging() -> None:
    """
    Set up application logging based on environment variables.
    
    Environment Variables:
        LOG_LEVEL: Logging level (default: INFO)
        LOG_FORMAT: Logging format - 'json' or 'text' (default: json)
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "json").lower()

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level, logging.INFO))

    # Set formatter based on settings
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set specific loggers to appropriate levels
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("databricks").setLevel(logging.INFO)

    root_logger.info(
        "Logging configured",
        extra={
            "level": log_level,
            "format": log_format,
        },
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class RequestIDFilter(logging.Filter):
    """
    Filter that adds request_id to log records.

    This is useful for tracing logs across a single request.
    """

    def __init__(self, request_id: str):
        """
        Initialize filter with request ID.

        Args:
            request_id: Unique request identifier
        """
        super().__init__()
        self.request_id = request_id

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add request_id to log record.

        Args:
            record: Log record to modify

        Returns:
            Always True (don't filter any records)
        """
        record.request_id = self.request_id
        return True


def add_request_id_to_logger(logger: logging.Logger, request_id: str) -> None:
    """
    Add a request ID filter to a logger.

    Args:
        logger: Logger to modify
        request_id: Request ID to add to all log records
    """
    request_filter = RequestIDFilter(request_id)
    logger.addFilter(request_filter)


def remove_request_id_from_logger(logger: logging.Logger) -> None:
    """
    Remove all RequestIDFilter instances from a logger.

    Args:
        logger: Logger to modify
    """
    logger.filters = [
        f for f in logger.filters if not isinstance(f, RequestIDFilter)
    ]
