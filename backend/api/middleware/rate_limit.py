"""
Rate Limiting Middleware for FastAPI.

Sliding-window rate limiter with optional burst allowance.
Requires Python 3.11+.
"""

from __future__ import annotations

import asyncio
import ipaddress
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any

from fastapi import HTTPException, Request, Response
from starlette.types import ASGIApp, Receive, Scope, Send

from utils.config import get_settings
from utils.logger import LoggerMixin


@dataclass(slots=True)
class RateLimitInfo:
    """Information about a rate limit decision."""

    limit: int
    remaining: int
    reset_at: float
    window: int
    allowed: bool = True


class RateLimiter(LoggerMixin):
    """Sliding window rate limiter keyed by client IP."""

    def __init__(self) -> None:
        settings = get_settings().api

        self.enabled = settings.rate_limit_enabled
        self.requests_per_window = settings.rate_limit_requests
        self.window_seconds = settings.rate_limit_window
        self.burst_allowance = settings.rate_limit_burst

        # Timestamps of accepted requests only (no burst-flag side effects)
        self._requests: dict[str, deque[float]] = {}
        self._lock = asyncio.Lock()

        if self.enabled:
            self.log.info(
                "rate_limiter_enabled",
                limit=self.requests_per_window,
                window=self.window_seconds,
                burst=self.burst_allowance,
            )

    async def is_allowed(self, client_ip: str) -> RateLimitInfo:
        """Return whether the client may proceed and remaining quota.

        Burst is additive: total capacity per window is
        ``requests_per_window + burst_allowance``. Burst tokens are only
        considered after the base quota is exhausted.
        """
        max_limit = self.requests_per_window + self.burst_allowance

        if not self.enabled:
            return RateLimitInfo(
                limit=max_limit,
                remaining=max_limit,
                reset_at=time.time() + self.window_seconds,
                window=self.window_seconds,
                allowed=True,
            )

        async with self._lock:
            current_time = time.time()

            if client_ip not in self._requests:
                self._requests[client_ip] = deque()

            requests = self._requests[client_ip]
            window_start = current_time - self.window_seconds
            while requests and requests[0] < window_start:
                requests.popleft()

            window_count = len(requests)
            reset_at = (
                requests[0] + self.window_seconds
                if requests
                else current_time + self.window_seconds
            )

            if window_count >= max_limit:
                self.log.warning(
                    "rate_limit_exceeded",
                    client_ip=client_ip,
                    window_count=window_count,
                )
                return RateLimitInfo(
                    limit=max_limit,
                    remaining=0,
                    reset_at=reset_at,
                    window=self.window_seconds,
                    allowed=False,
                )

            requests.append(current_time)
            remaining = max(0, max_limit - len(requests))
            # Keep reset_at consistent with rejection path after append
            reset_at = requests[0] + self.window_seconds

            return RateLimitInfo(
                limit=max_limit,
                remaining=remaining,
                reset_at=reset_at,
                window=self.window_seconds,
                allowed=True,
            )

    async def cleanup_old_entries(self) -> None:
        """Drop stale per-IP windows to bound memory."""
        async with self._lock:
            current_time = time.time()
            cutoff_time = current_time - (self.window_seconds * 2)

            for client_ip in list(self._requests.keys()):
                requests = self._requests[client_ip]
                while requests and requests[0] < cutoff_time:
                    requests.popleft()
                if not requests:
                    del self._requests[client_ip]


def _peer_ip(scope: Scope) -> str | None:
    client = scope.get("client")
    if client and isinstance(client, (list, tuple)) and len(client) > 0:
        return str(client[0])
    return None


def _ip_in_trusted(peer: str, trusted: list[str]) -> bool:
    """Return True if peer is in any trusted host/CIDR entry."""
    try:
        peer_addr = ipaddress.ip_address(peer)
    except ValueError:
        return peer in trusted

    for entry in trusted:
        try:
            if "/" in entry:
                if peer_addr in ipaddress.ip_network(entry, strict=False):
                    return True
            elif peer_addr == ipaddress.ip_address(entry):
                return True
        except ValueError:
            if peer == entry:
                return True
    return False


class RateLimitMiddleware:
    """ASGI middleware that enforces RateLimiter and emits X-RateLimit-* headers."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._limiter = RateLimiter()
        self._trusted_proxies = list(get_settings().api.trusted_proxies)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        client_ip = self._get_client_ip(scope)
        limit_info = await self._limiter.is_allowed(client_ip)

        if not limit_info.allowed:
            response = Response(
                content='{"error": "Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
                headers={
                    "X-RateLimit-Limit": str(limit_info.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(limit_info.reset_at)),
                    "Retry-After": str(max(0, int(limit_info.reset_at - time.time()))),
                },
            )
            await response(scope, receive, send)
            return

        async def send_with_headers(message: dict[str, Any]) -> None:
            if message.get("type") == "http.response.start":
                headers = list(message.get("headers") or [])
                headers.extend(
                    [
                        (b"x-ratelimit-limit", str(limit_info.limit).encode()),
                        (
                            b"x-ratelimit-remaining",
                            str(max(0, limit_info.remaining)).encode(),
                        ),
                        (b"x-ratelimit-reset", str(int(limit_info.reset_at)).encode()),
                    ]
                )
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_headers)

    def _get_client_ip(self, scope: Scope) -> str:
        """Use socket peer by default; honor XFF only from trusted proxies."""
        peer = _peer_ip(scope)
        if peer is None:
            return "unknown"

        if not self._trusted_proxies or not _ip_in_trusted(peer, self._trusted_proxies):
            return peer

        raw_headers = scope.get("headers") or []
        headers = {
            k.decode("latin-1").lower(): v.decode("latin-1")
            for k, v in raw_headers
            if isinstance(k, (bytes, bytearray))
        }
        for header in ("x-forwarded-for", "x-real-ip"):
            if header in headers:
                # Rightmost client before proxies is safest with known hop count=1
                return headers[header].split(",")[0].strip() or peer
        return peer


def rate_limit(
    requests_per_window: int | None = None,
    window_seconds: int | None = None,
) -> Callable[..., Any]:
    """Decorator for tighter per-route limits (uses a dedicated limiter instance)."""
    settings = get_settings().api

    limiter = RateLimiter()
    if requests_per_window is not None:
        limiter.requests_per_window = requests_per_window
    if window_seconds is not None:
        limiter.window_seconds = window_seconds
    _ = settings  # keep settings read for future route-level defaults

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if request is None:
                request = kwargs.get("request")

            if not request:
                return await func(*args, **kwargs)

            client_ip = request.client.host if request.client else "unknown"
            limit_info = await limiter.is_allowed(client_ip)

            if not limit_info.allowed:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(limit_info.limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(limit_info.reset_at)),
                        "Retry-After": str(
                            max(0, int(limit_info.reset_at - time.time()))
                        ),
                    },
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
