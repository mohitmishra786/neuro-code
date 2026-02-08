"""
Tests for Request ID Middleware.

Verifies that request IDs are properly generated, propagated, and included in logs.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestRequestIDMiddleware:
    """Test cases for RequestIDMiddleware."""

    def test_request_id_generated_if_not_provided(self) -> None:
        """Test that a request ID is generated when not provided."""
        from api.middleware.request_id import RequestIDMiddleware

        app = FastAPI()

        @app.get("/test")
        async def test_endpoint() -> dict:
            from api.middleware.request_id import get_request_id
            return {"request_id": get_request_id()}

        app.add_middleware(RequestIDMiddleware)

        with TestClient(app) as client:
            response = client.get("/test")
            assert response.status_code == 200
            data = response.json()
            assert data["request_id"] is not None
            assert len(data["request_id"]) == 36

    def test_request_id_from_header_used(self) -> None:
        """Test that provided request ID header is used."""
        from api.middleware.request_id import RequestIDMiddleware

        app = FastAPI()

        @app.get("/test")
        async def test_endpoint() -> dict:
            from api.middleware.request_id import get_request_id
            return {"request_id": get_request_id()}

        app.add_middleware(RequestIDMiddleware)

        with TestClient(app) as client:
            custom_id = "custom-request-id-123"
            response = client.get("/test", headers={"X-Request-ID": custom_id})
            assert response.status_code == 200
            data = response.json()
            assert data["request_id"] == custom_id

    def test_request_id_in_response_header(self) -> None:
        """Test that request ID is returned in response headers."""
        from api.middleware.request_id import RequestIDMiddleware

        app = FastAPI()

        @app.get("/test")
        async def test_endpoint() -> dict:
            return {"status": "ok"}

        app.add_middleware(RequestIDMiddleware)

        with TestClient(app) as client:
            response = client.get("/test")
            assert response.status_code == 200
            assert "X-Request-ID" in response.headers
            assert len(response.headers["X-Request-ID"]) == 36

    def test_get_request_id_returns_none_outside_context(self) -> None:
        """Test that get_request_id returns None when not in request context."""
        from api.middleware.request_id import get_request_id

        result = get_request_id()
        assert result is None

    def test_bind_request_id_works(self) -> None:
        """Test that bind_request_id adds ID to context."""
        from api.middleware.request_id import bind_request_id, get_request_id

        bind_request_id("test-id-123")
        result = get_request_id()
        assert result == "test-id-123"
