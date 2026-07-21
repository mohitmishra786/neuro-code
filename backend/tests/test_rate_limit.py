"""Tests for rate limiter burst semantics and IP keying."""

from __future__ import annotations

import pytest

from api.middleware.rate_limit import RateLimiter, _ip_in_trusted


@pytest.mark.asyncio
async def test_burst_allows_beyond_base_quota() -> None:
    """Burst is additive: can accept requests_per_window + burst_allowance."""
    limiter = RateLimiter()
    limiter.enabled = True
    limiter.requests_per_window = 5
    limiter.burst_allowance = 3
    limiter.window_seconds = 60

    allowed = 0
    for _ in range(20):
        info = await limiter.is_allowed("1.2.3.4")
        if info.allowed:
            allowed += 1
        else:
            break

    assert allowed == 8  # 5 base + 3 burst
    deny = await limiter.is_allowed("1.2.3.4")
    assert deny.allowed is False
    assert deny.remaining == 0


def test_trusted_proxy_cidr() -> None:
    assert _ip_in_trusted("10.0.0.5", ["10.0.0.0/8"]) is True
    assert _ip_in_trusted("11.0.0.5", ["10.0.0.0/8"]) is False
    assert _ip_in_trusted("127.0.0.1", ["127.0.0.1"]) is True
