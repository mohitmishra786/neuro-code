"""
Rate Limiting Middleware for FastAPI.

Implements token bucket algorithm for API rate limiting.
Requires Python 3.11+.
"""

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from functools import wraps
from typing import Callable, Awaitable

from fastapi import HTTPException, Request, Response
from fastapi.types import ASGIAppCallable

from utils.config import get_settings
from utils.logger import LoggerMixin


@dataclass
class RateLimitInfo:
    """Information about a rate limit."""
    
    limit: int
    remaining: int
    reset_at: float
    window: int


class RateLimiter(LoggerMixin):
    """
    Token bucket rate limiter.

    Uses sliding window algorithm to limit request rate per client.
    """

    def __init__(self) -> None:
        """Initialize the rate limiter."""
        settings = get_settings().api
        
        self.enabled = settings.rate_limit_enabled
        self.requests_per_window = settings.rate_limit_requests
        self.window_seconds = settings.rate_limit_window
        self.burst_allowance = settings.rate_limit_burst
        
        # Track requests per client (IP address)
        # Structure: {ip: deque of (timestamp, burst_count)}
        self._requests: dict[str, deque[tuple[float, int]]] = {}
        self._lock = asyncio.Lock()
        
        if self.enabled:
            self.log.info(
                "rate_limiter_enabled",
                limit=self.requests_per_window,
                window=self.window_seconds,
                burst=self.burst_allowance,
            )

    async def is_allowed(self, client_ip: str) -> RateLimitInfo:
        """
        Check if request from client is allowed.

        Args:
            client_ip: Client IP address

        Returns:
            RateLimitInfo with limit status
        """
        if not self.enabled:
            return RateLimitInfo(
                limit=self.requests_per_window,
                remaining=self.requests_per_window,
                reset_at=time.time() + self.window_seconds,
                window=self.window_seconds,
            )

        async with self._lock:
            current_time = time.time()
            
            # Get or create request deque for this client
            if client_ip not in self._requests:
                self._requests[client_ip] = deque()
            
            requests = self._requests[client_ip]
            
            # Remove requests outside the window
            window_start = current_time - self.window_seconds
            while requests and requests[0][0] < window_start:
                requests.popleft()
            
            # Count requests in window, accounting for burst
            window_count = len(requests)
            
            # Calculate burst tokens available
            burst_used = sum(1 for _, burst in requests if burst > 1)
            burst_remaining = max(0, self.burst_allowance - burst_used)
            effective_limit = self.requests_per_window + burst_remaining
            
            remaining = effective_limit - window_count
            
            if remaining < 0:
                # Rate limit exceeded
                # Find when the oldest request will fall out of window
                if requests:
                    reset_at = requests[0][0] + self.window_seconds
                else:
                    reset_at = current_time + self.window_seconds
                
                self.log.warning(
                    "rate_limit_exceeded",
                    client_ip=client_ip,
                    window_count=window_count,
                )
                
                return RateLimitInfo(
                    limit=effective_limit,
                    remaining=0,
                    reset_at=reset_at,
                    window=self.window_seconds,
                )
            
            # Add this request
            burst_usage = min(burst_remaining, 1)
            requests.append((current_time, burst_usage))
            
            return RateLimitInfo(
                limit=effective_limit,
                remaining=remaining,
                reset_at=window_start + self.window_seconds,
                window=self.window_seconds,
            )

    def cleanup_old_entries(self) -> None:
        """
        Clean up old entries from rate limit tracking.

        Should be called periodically to prevent memory buildup.
        """
        async with self._lock:
            current_time = time.time()
            cutoff_time = current_time - (self.window_seconds * 2)
            
            # Remove entries older than 2x the window
            for client_ip in list(self._requests.keys()):
                requests = self._requests[client_ip]
                while requests and requests[0][0] < cutoff_time:
                    requests.popleft()
                
                # Remove clients with no recent requests
                if not requests:
                    del self._requests[client_ip]


class RateLimitMiddleware:
    """
    FastAPI middleware for rate limiting.

    Adds rate limit headers and enforces limits.
    """

    def __init__(self, app: ASGIAppCallable) -> None:
        """
        Initialize middleware.

        Args:
            app: ASGI application to wrap
        """
        self.app = app
        self._limiter = RateLimiter()

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        """
        Process incoming request with rate limiting.

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Get client IP
        client_ip = self._get_client_ip(scope)

        # Check rate limit
        limit_info = await self._limiter.is_allowed(client_ip)

        if limit_info.remaining < 0:
            # Rate limit exceeded - return 429
            response = Response(
                content='{"error": "Rate limit exceeded"}',
                status_code=429,
                headers={
                    "X-RateLimit-Limit": str(limit_info.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(limit_info.reset_at)),
                    "Retry-After": str(int(limit_info.reset_at - time.time())),
                },
            )
            await response(scope, receive, send)
            return

        # Add rate limit headers to response
        async def send_with_headers(message: dict[str, Any]) -> None:
            headers = message.get("headers", {})
            headers.update({
                "X-RateLimit-Limit": str(limit_info.limit),
                "X-RateLimit-Remaining": str(limit_info.remaining),
                "X-RateLimit-Reset": str(int(limit_info.reset_at)),
            })
            message["headers"] = headers
            await send(message)

        # Process request with modified send function
        await self.app(scope, receive, send_with_headers)

    def _get_client_ip(self, scope: dict) -> str:
        """
        Extract client IP address from ASGI scope.

        Args:
            scope: ASGI scope dictionary

        Returns:
            Client IP address as string
        """
        # Check for forwarded headers (proxy/load balancer)
        for header in ["x-forwarded-for", "x-real-ip"]:
            if header in scope.get("headers", {}):
                forwarded = scope["headers"][header]
                if isinstance(forwarded, list):
                    forwarded = forwarded[0]
                # Get first IP if multiple
                ip = forwarded.split(",")[0].strip()
                return ip

        # Fall back to direct connection IP
        client = scope.get("client", {})
        if isinstance(client, (list, tuple)):
            client = client[0] if client else None
        if client:
            return str(client.get("host", "unknown"))

        return "unknown"


def rate_limit(
    requests_per_window: int | None = None,
    window_seconds: int | None = None,
) -> Callable:
    """
    Decorator for rate limiting specific endpoints.

    Args:
        requests_per_window: Custom limit (uses default from config if None)
        window_seconds: Custom window (uses default from config if None)

    Returns:
        Decorator function
    """
    settings = get_settings().api
    
    limit = requests_per_window if requests_per_window is not None else settings.rate_limit_requests
    window = window_seconds if window_seconds is not None else settings.rate_limit_window
    burst = settings.rate_limit_burst
    
    limiter = RateLimiter()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs or args
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                return await func(*args, **kwargs)

            # Get client IP
            client_ip = request.client.host if request.client else "unknown"

            # Check rate limit
            limit_info = await limiter.is_allowed(client_ip)

            if limit_info.remaining < 0:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(limit_info.limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(limit_info.reset_at)),
                        "Retry-After": str(int(limit_info.reset_at - time.time())),
                    },
                )

            # Execute function
            return await func(*args, **kwargs)

        return wrapper

    return decorator
