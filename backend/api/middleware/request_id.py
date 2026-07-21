"""
Request ID Middleware for Distributed Tracing.

Adds unique request IDs to all incoming requests for tracing across async operations.
Requires Python 3.11+.
"""

import uuid
from typing import Any

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

structlog.contextvars.clear_contextvars()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds a unique request ID to each incoming request.

    The request ID is:
    - Generated for each request if not provided
    - Added to response headers (X-Request-ID)
    - Bound to structlog context for consistent logging
    """

    HEADER_NAME = "X-Request-ID"
    CONTEXT_KEY = "request_id"

    def __init__(self, app: ASGIApp) -> None:
        """
        Initialize the middleware.

        Args:
            app: ASGI application to wrap
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """
        Process request and add tracing ID.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response with request ID header
        """
        request_id = request.headers.get(self.HEADER_NAME) or str(uuid.uuid4())

        structlog.contextvars.bind_contextvars(
            request_id=request_id,
        )

        response = await call_next(request)

        response.headers[self.HEADER_NAME] = request_id

        return response


def get_request_id() -> str | None:
    """
    Get the current request ID from context.

    Returns:
        Current request ID or None if not in request context
    """
    # structlog >=24 uses get_contextvars(); older docs mentioned get_context_var
    ctx = structlog.contextvars.get_contextvars()
    value = ctx.get(RequestIDMiddleware.CONTEXT_KEY)
    return value if isinstance(value, str) else None


def bind_request_id(request_id: str) -> None:
    """
    Bind a request ID to the current context.

    Args:
        request_id: The request ID to bind
    """
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
    )
