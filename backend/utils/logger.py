"""
NeuroCode Structured Logging Module.

Provides consistent, structured logging throughout the application.
Requires Python 3.11+.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from utils.config import get_settings


def _add_app_context(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add application context to all log entries."""
    settings = get_settings()
    event_dict["app"] = settings.app_name
    event_dict["version"] = settings.app_version
    event_dict["environment"] = settings.environment
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

    Usage:
        class MyClass(LoggerMixin):
            def my_method(self):
                self.log.info("doing something", key="value")
    """

    @property
    def log(self) -> structlog.stdlib.BoundLogger:
        """Get logger bound to this class name."""
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger
