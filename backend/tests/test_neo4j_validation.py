"""
Tests for Neo4j Client Validation.

Requires Python 3.11+.
connect() is graceful: returns False on bad config / auth failure (does not raise).
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from graph_db.neo4j_client import Neo4jClient
from utils.config import Neo4jSettings


class TestNeo4jCredentialValidation:
    """Test cases for Neo4j credential validation."""

    @pytest.fixture
    def mock_driver(self):
        """Create a mock Neo4j driver."""
        driver = MagicMock()
        driver.verify_connectivity = AsyncMock()
        driver.session = MagicMock()

        mock_session = MagicMock()
        mock_session.run = AsyncMock()
        mock_session.close = AsyncMock()
        driver.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        driver.session.return_value.__aexit__ = AsyncMock()

        driver.close = AsyncMock()
        return driver

    @pytest.mark.asyncio
    async def test_connect_with_default_password_returns_false(self) -> None:
        settings = Neo4jSettings(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password",
        )
        with patch("graph_db.neo4j_client.get_settings") as mock_get_settings:
            mock_get_settings.return_value.neo4j = settings
            client = Neo4jClient()
            assert await client.connect() is False

    @pytest.mark.asyncio
    async def test_connect_with_empty_password_returns_false(self) -> None:
        settings = Neo4jSettings(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="",
        )
        with patch("graph_db.neo4j_client.get_settings") as mock_get_settings:
            mock_get_settings.return_value.neo4j = settings
            client = Neo4jClient()
            assert await client.connect() is False

    @pytest.mark.asyncio
    async def test_connect_with_missing_uri_returns_false(self) -> None:
        settings = Neo4jSettings(
            uri="",
            user="neo4j",
            password="realpassword",
        )
        with patch("graph_db.neo4j_client.get_settings") as mock_get_settings:
            mock_get_settings.return_value.neo4j = settings
            client = Neo4jClient()
            assert await client.connect() is False

    @pytest.mark.asyncio
    async def test_connect_with_missing_user_returns_false(self) -> None:
        settings = Neo4jSettings(
            uri="bolt://localhost:7687",
            user="",
            password="realpassword",
        )
        with patch("graph_db.neo4j_client.get_settings") as mock_get_settings:
            mock_get_settings.return_value.neo4j = settings
            client = Neo4jClient()
            assert await client.connect() is False

    @pytest.mark.asyncio
    async def test_connect_with_valid_credentials_succeeds(self, mock_driver) -> None:
        settings = Neo4jSettings(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="realpassword",
        )
        with (
            patch("graph_db.neo4j_client.get_settings") as mock_get_settings,
            patch("graph_db.neo4j_client.AsyncGraphDatabase.driver") as mock_create_driver,
        ):
            mock_get_settings.return_value.neo4j = settings
            mock_create_driver.return_value = mock_driver
            client = Neo4jClient()
            assert await client.connect() is True
            mock_driver.verify_connectivity.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_with_auth_failure_returns_false(self, mock_driver) -> None:
        settings = Neo4jSettings(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="wrongpassword",
        )
        mock_driver.verify_connectivity = AsyncMock(
            side_effect=Exception("Authentication failed for user 'neo4j'")
        )
        with (
            patch("graph_db.neo4j_client.get_settings") as mock_get_settings,
            patch("graph_db.neo4j_client.AsyncGraphDatabase.driver") as mock_create_driver,
        ):
            mock_get_settings.return_value.neo4j = settings
            mock_create_driver.return_value = mock_driver
            client = Neo4jClient()
            assert await client.connect() is False
            mock_driver.close.assert_called()

    @pytest.mark.asyncio
    async def test_connect_on_auth_failure_closes_driver(self, mock_driver) -> None:
        settings = Neo4jSettings(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="wrongpassword",
        )
        mock_driver.verify_connectivity = AsyncMock(
            side_effect=Exception("Unauthorized access")
        )
        with (
            patch("graph_db.neo4j_client.get_settings") as mock_get_settings,
            patch("graph_db.neo4j_client.AsyncGraphDatabase.driver") as mock_create_driver,
        ):
            mock_get_settings.return_value.neo4j = settings
            mock_create_driver.return_value = mock_driver
            client = Neo4jClient()
            assert await client.connect() is False
            mock_driver.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_connect_calls_reuse_driver(self, mock_driver) -> None:
        settings = Neo4jSettings(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="realpassword",
        )
        with (
            patch("graph_db.neo4j_client.get_settings") as mock_get_settings,
            patch("graph_db.neo4j_client.AsyncGraphDatabase.driver") as mock_create_driver,
        ):
            mock_get_settings.return_value.neo4j = settings
            mock_create_driver.return_value = mock_driver
            client = Neo4jClient()
            assert await client.connect() is True
            assert await client.connect() is True
            mock_create_driver.assert_called_once()
