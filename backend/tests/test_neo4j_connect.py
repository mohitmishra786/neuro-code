"""
Tests for Neo4jClient connectivity improvements.

Verifies that Neo4j connection is non-blocking with timeout support.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestNeo4jClientConnect:
    """Test cases for Neo4jClient.connect() with timeout."""

    @pytest.fixture
    def mock_driver(self) -> MagicMock:
        """Create a mock Neo4j driver."""
        driver = MagicMock()
        driver.verify_connectivity = AsyncMock()
        driver.session.return_value.__aenter__ = AsyncMock()
        driver.session.return_value.__aexit__ = AsyncMock()
        driver.session.return_value.run = AsyncMock()
        driver.close = AsyncMock()
        return driver

    @pytest.mark.asyncio
    async def test_connect_returns_true_on_success(self, mock_driver: MagicMock) -> None:
        """Test that connect returns True when successful."""
        from graph_db.neo4j_client import Neo4jClient

        mock_session = MagicMock()
        mock_session.run = AsyncMock()
        mock_driver.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_driver.session.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "graph_db.neo4j_client.AsyncGraphDatabase.driver", return_value=mock_driver
        ):
            client = Neo4jClient()
            client._settings = MagicMock()
            client._settings.uri = "bolt://localhost:7687"
            client._settings.user = "neo4j"
            client._settings.password = "secure-test-password"
            client._settings.database = "neo4j"
            client._settings.max_connection_pool_size = 10
            result = await client.connect(timeout=5.0)

            assert result is True
            mock_driver.verify_connectivity.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_connect_returns_false_on_timeout(self) -> None:
        """Test that connect returns False on timeout."""
        from graph_db.neo4j_client import Neo4jClient

        mock_driver = MagicMock()
        mock_driver.verify_connectivity = AsyncMock(side_effect=TimeoutError())
        mock_driver.close = AsyncMock()

        with patch(
            "graph_db.neo4j_client.AsyncGraphDatabase.driver", return_value=mock_driver
        ):
            client = Neo4jClient()
            client._settings = MagicMock()
            client._settings.uri = "bolt://localhost:7687"
            client._settings.user = "neo4j"
            client._settings.password = "secure-test-password"
            client._settings.database = "neo4j"
            client._settings.max_connection_pool_size = 10
            result = await client.connect(timeout=1.0)

            assert result is False
            mock_driver.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_connect_returns_false_on_invalid_credentials(self) -> None:
        """Test that connect returns False on invalid credentials."""
        from graph_db.neo4j_client import Neo4jClient

        client = Neo4jClient()
        client._settings = MagicMock()
        client._settings.uri = "bolt://localhost:7687"
        client._settings.user = "neo4j"
        client._settings.password = "password"  # Default weak password
        client._settings.database = "neo4j"

        result = await client.connect(timeout=5.0)

        assert result is False

    @pytest.mark.asyncio
    async def test_connect_returns_false_on_missing_config(self) -> None:
        """Test that connect returns False when config is incomplete."""
        from graph_db.neo4j_client import Neo4jClient

        client = Neo4jClient()
        client._settings = MagicMock()
        client._settings.uri = None
        client._settings.user = None

        result = await client.connect(timeout=5.0)

        assert result is False
