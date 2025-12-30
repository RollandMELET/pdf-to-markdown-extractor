"""
PDF-to-Markdown Extractor - Logging Configuration.

Centralized logging configuration using loguru with structured JSON output,
log rotation, and environment-based configuration.
"""

import os
import sys
from pathlib import Path
from typing import Optional

from loguru import logger


# ==========================================
# Environment Configuration
# ==========================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # "json" or "text"
LOG_DIR = Path(os.getenv("LOG_DIR", "/app/logs"))
LOG_ROTATION = os.getenv("LOG_ROTATION", "100 MB")  # Rotate when file reaches size
LOG_RETENTION = os.getenv("LOG_RETENTION", "30 days")  # Keep logs for duration
LOG_COMPRESSION = os.getenv("LOG_COMPRESSION", "zip")  # Compression format


# ==========================================
# Log Formats
# ==========================================

# JSON format for production (machine-readable, structured)
JSON_FORMAT = (
    '{{'
    '"timestamp": "{time:YYYY-MM-DD HH:mm:ss.SSS}",'
    '"level": "{level}",'
    '"logger": "{name}",'
    '"function": "{function}",'
    '"line": {line},'
    '"message": "{message}",'
    '"extra": {extra}'
    '}}'
)

# Human-readable format for development
TEXT_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


# ==========================================
# Logging Configuration
# ==========================================

def setup_logging(
    level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_dir: Optional[Path] = None,
    enable_file_logging: bool = True,
) -> None:
    """
    Configure loguru logger with structured logging.

    This function should be called once at application startup to configure
    the global logger instance.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               If not provided, uses LOG_LEVEL environment variable.
        log_format: Output format ("json" or "text").
                   If not provided, uses LOG_FORMAT environment variable.
        log_dir: Directory for log files.
                If not provided, uses LOG_DIR environment variable.
        enable_file_logging: Whether to enable file-based logging.
                            Defaults to True.

    Example:
        >>> from src.utils.logging_config import setup_logging
        >>> setup_logging(level="INFO", log_format="json")
        >>> from loguru import logger
        >>> logger.info("Application started", extra={"version": "1.0.0"})
    """
    # Use provided values or fall back to environment variables
    level = level or LOG_LEVEL
    log_format = log_format or LOG_FORMAT
    log_dir = log_dir or LOG_DIR

    # Remove default logger
    logger.remove()

    # Determine format string
    format_string = JSON_FORMAT if log_format.lower() == "json" else TEXT_FORMAT

    # Add stdout handler (always enabled for container logs)
    logger.add(
        sys.stdout,
        format=format_string,
        level=level,
        colorize=(log_format.lower() == "text"),  # Only colorize text format
        serialize=(log_format.lower() == "json"),  # Serialize to JSON if json format
        backtrace=True,
        diagnose=True,
    )

    # Add file logging if enabled
    if enable_file_logging:
        # Ensure log directory exists
        log_dir.mkdir(parents=True, exist_ok=True)

        # General application log (all levels)
        logger.add(
            log_dir / "app.log",
            format=JSON_FORMAT,  # Always use JSON for file logs
            level=level,
            rotation=LOG_ROTATION,
            retention=LOG_RETENTION,
            compression=LOG_COMPRESSION,
            serialize=True,  # Always serialize file logs to JSON
            backtrace=True,
            diagnose=True,
        )

        # Error log (ERROR and CRITICAL only)
        logger.add(
            log_dir / "errors.log",
            format=JSON_FORMAT,
            level="ERROR",
            rotation=LOG_ROTATION,
            retention=LOG_RETENTION,
            compression=LOG_COMPRESSION,
            serialize=True,
            backtrace=True,
            diagnose=True,
        )

    logger.info(
        f"Logging configured: level={level}, format={log_format}, "
        f"file_logging={enable_file_logging}"
    )


def get_logger():
    """
    Get the configured logger instance.

    Returns:
        logger: Configured loguru logger instance.

    Example:
        >>> from src.utils.logging_config import get_logger
        >>> logger = get_logger()
        >>> logger.info("Hello world")
    """
    return logger


# ==========================================
# Context Processors
# ==========================================

def add_request_context(request_id: str, user_id: Optional[str] = None):
    """
    Add request context to all subsequent log messages.

    This is useful for tracking logs related to a specific request
    across multiple function calls.

    Args:
        request_id: Unique request identifier.
        user_id: Optional user identifier.

    Returns:
        Context manager for use with 'with' statement.

    Example:
        >>> with add_request_context("req-123", "user-456"):
        ...     logger.info("Processing request")
        # Output includes request_id and user_id in extra fields
    """
    context = {"request_id": request_id}
    if user_id:
        context["user_id"] = user_id
    return logger.contextualize(**context)


def add_task_context(task_id: str, task_name: str):
    """
    Add Celery task context to log messages.

    Args:
        task_id: Celery task ID.
        task_name: Task name.

    Returns:
        Context manager for use with 'with' statement.

    Example:
        >>> with add_task_context("task-123", "extract_pdf"):
        ...     logger.info("Task started")
    """
    return logger.contextualize(task_id=task_id, task_name=task_name)


# ==========================================
# Interceptor for Standard Library Logging
# ==========================================

class InterceptHandler:
    """
    Intercept standard library logging and redirect to loguru.

    This is useful for libraries that use the standard logging module
    (like uvicorn, FastAPI, etc.) to ensure all logs go through loguru.
    """

    def write(self, message: str):
        """Intercept and redirect log messages."""
        # Get the caller's frame to determine the log level
        try:
            level = logger.level(message.split("|")[1].strip()).name
        except Exception:
            level = "INFO"

        logger.opt(depth=6, exception=False).log(level, message.rstrip())


def setup_intercept_handler():
    """
    Setup handler to intercept standard library logging.

    This should be called after setup_logging() if you want to
    capture logs from libraries using the standard logging module.

    Example:
        >>> from src.utils.logging_config import setup_logging, setup_intercept_handler
        >>> setup_logging()
        >>> setup_intercept_handler()
    """
    import logging

    # Intercept everything from standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


# ==========================================
# Auto-configure on import (optional)
# ==========================================

# Uncomment the following line to auto-configure logging on module import
# This is useful if you want logging to be configured automatically
# setup_logging()
