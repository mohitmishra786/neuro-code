"""
NeuroCode Structured Logging Module.

Provides consistent, structured logging throughout the application.
Requires Python 3.11+.
"""

import logging
import re
import sys
from typing import Any

import structlog
from structlog.types import Processor

from utils.config import get_settings


_sensitive_keys = {"password", "token", "secret", "api_key", "private_key", "access_token", "refresh_token", "credentials", "auth"}

_app_context_cache: dict[str, str] | None = None


LOG_LEVEL_MAP: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def _get_log_level(level: str) -> int:
    """Get standardized log level integer from string."""
    return LOG_LEVEL_MAP.get(level.upper(), logging.INFO)


def _get_app_context() -> dict[str, str]:
    """Get cached app context to avoid repeated settings lookups."""
    global _app_context_cache
    if _app_context_cache is None:
        settings = get_settings()
        _app_context_cache = {
            "app": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        }
    return _app_context_cache


def _sanitize_value(key: str, value: Any) -> Any:
    """Sanitize sensitive values in logs."""
    if isinstance(value, dict):
        return {k: _sanitize_value(k, v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return [_sanitize_value(key, v) for v in value]
    elif key.lower() in _sensitive_keys:
        return "***REDACTED***"
    return value


def _sanitize_event_dict(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Sanitize sensitive data from event dict."""
    return {k: _sanitize_value(k, v) for k, v in event_dict.items()}


def _add_app_context(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add application context to all log entries."""
    event_dict.update(_get_app_context())
    return event_dict


def _extract_from_record(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Extract useful info from the log record if present."""
    record = event_dict.get("_record")
    if record is not None:
        event_dict["filename"] = record.filename
        event_dict["lineno"] = record.lineno
        event_dict["func_name"] = record.funcName
    return event_dict


def configure_logging() -> None:
    """
    Configure structured logging for the application.

    Call this once at application startup.
    """
    settings = get_settings()

    # Common processors for all output formats
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        _sanitize_event_dict,
        _add_app_context,
    ]

    if settings.logging.format == "json":
        # JSON format for production
        processors: list[Processor] = [
            *shared_processors,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Console format for development
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.logging.level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.logging.level.upper()),
    )

    # Suppress noisy loggers
    logging.getLogger("neo4j").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("watchdog").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__ of the calling module)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


# Pre-configured logger for quick imports
logger = get_logger("neurocode")


class LoggerMixin:
    """
    Mixin class to add logging capability to any class.

    Uses name-mangled private attribute to prevent subclasses from
    accidentally overwriting the logger instance.

    Usage:
        class MyClass(LoggerMixin):
            def my_method(self):
                self.log.info("doing something", key="value")
    """

    @property
    def log(self) -> structlog.stdlib.BoundLogger:
        """Get logger bound to this class name."""
        cls_name = self.__class__.__name__
        mangled_attr = f"_LoggerMixin__log_{cls_name.replace('.', '_')}"
        if not hasattr(self, mangled_attr):
            setattr(self, mangled_attr, get_logger(cls_name))
        return getattr(self, mangled_attr)
