"""
Tests for Neo4jClient lifecycle and leak prevention.

Verifies that Neo4j connections are properly managed and cleaned up.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestNeo4jClientLifecycle:
    """Test cases for Neo4jClient lifecycle management."""

    @pytest.fixture(autouse=True)
    def reset_instances(self) -> None:
        """Reset instance tracking before each test."""
        from graph_db.neo4j_client import Neo4jClient
        Neo4jClient._instances.clear()
        yield
        # Cleanup after test
        asyncio.run(Neo4jClient.close_all())

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
    async def test_instance_tracking_on_creation(self) -> None:
        """Test that new instances are tracked."""
        from graph_db.neo4j_client import Neo4jClient

        client = Neo4jClient()
        instances = Neo4jClient.get_active_instances()

        assert client in instances
        assert len(instances) == 1

    @pytest.mark.asyncio
    async def test_instance_removal_on_close(self) -> None:
        """Test that closed instances are removed from tracking."""
        from graph_db.neo4j_client import Neo4jClient

        client = Neo4jClient()
        assert client in Neo4jClient.get_active_instances()

        await client.close()

        assert client not in Neo4jClient.get_active_instances()
        assert client._closed is True

    @pytest.mark.asyncio
    async def test_close_all_instances(self) -> None:
        """Test closing all active instances."""
        from graph_db.neo4j_client import Neo4jClient

        client1 = Neo4jClient()
        client2 = Neo4jClient()

        assert len(Neo4jClient.get_active_instances()) == 2

        await Neo4jClient.close_all()

        assert len(Neo4jClient.get_active_instances()) == 0

    @pytest.mark.asyncio
    async def test_idempotent_close(self) -> None:
        """Test that closing multiple times is safe."""
        from graph_db.neo4j_client import Neo4jClient

        client = Neo4jClient()
        mock_driver = MagicMock()
        mock_driver.close = AsyncMock()
        client._driver = mock_driver

        await client.close()
        await client.close()
        await client.close()

        assert client._closed is True
        mock_driver.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_garbage_collection_cleanup(self) -> None:
        """Test that explicit close removes instance tracking (GC is not guaranteed)."""
        from graph_db.neo4j_client import Neo4jClient

        client = Neo4jClient()
        assert client in Neo4jClient.get_active_instances()

        await client.close()
        assert len(Neo4jClient.get_active_instances()) == 0

    @pytest.mark.asyncio
    async def test_connect_failure_does_not_trap_instance(self) -> None:
        """Test that failed connect still allows proper cleanup."""
        from graph_db.neo4j_client import Neo4jClient

        client = Neo4jClient()
        client._settings = MagicMock()
        client._settings.uri = None
        client._settings.user = None

        # Don't connect - just close
        await client.close()

        assert client._closed is True
        assert len(Neo4jClient.get_active_instances()) == 0

    @pytest.mark.asyncio
    async def test_multiple_instances_independent(self) -> None:
        """Test that multiple instances are managed independently."""
        from graph_db.neo4j_client import Neo4jClient

        client1 = Neo4jClient()
        client2 = Neo4jClient()

        mock_driver1 = MagicMock()
        mock_driver1.close = AsyncMock()
        client1._driver = mock_driver1

        mock_driver2 = MagicMock()
        mock_driver2.close = AsyncMock()
        client2._driver = mock_driver2

        # Close only one
        await client1.close()

        assert client1._closed is True
        assert client2._closed is False
        assert client1 not in Neo4jClient.get_active_instances()
        assert client2 in Neo4jClient.get_active_instances()

        mock_driver1.close.assert_awaited_once()
        mock_driver2.close.assert_not_awaited()
