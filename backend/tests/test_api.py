"""
Tests for API Routes.

Requires Python 3.11+.
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test cases for health endpoint."""

    def test_health_check(self, client):
        """Test health check returns valid response."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "version" in data


class TestGraphEndpoints:
    """Test cases for graph endpoints."""

    def test_get_root_nodes_no_db(self, client):
        """Test root nodes endpoint without database."""
        response = client.get("/graph/root")
        # May return 503 if no database, or 200 with empty list
        assert response.status_code in [200, 503]

    def test_get_node_not_found(self, client):
        """Test getting a non-existent node."""
        response = client.get("/graph/node/nonexistent-id")
        assert response.status_code in [404, 503]


class TestSearchEndpoints:
    """Test cases for search endpoints."""

    def test_search_empty_query(self, client):
        """Test search with empty query."""
        response = client.get("/search?q=")
        # Should return 422 (validation error) for empty query
        assert response.status_code == 422

    def test_search_valid_query(self, client):
        """Test search with valid query."""
        response = client.get("/search?q=test")
        # May return 503 if no database
        assert response.status_code in [200, 503]
