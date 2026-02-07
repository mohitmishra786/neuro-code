"""
Tests for Neo4j Client Validation.

Requires Python 3.11+.
"""

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
    async def test_connect_with_default_password_raises_error(self):
        """Test that connecting with default password raises ValueError."""
        settings = Neo4jSettings(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password"
        )
        
        with patch("graph_db.neo4j_client.get_settings") as mock_get_settings:
            mock_get_settings.return_value.neo4j = settings
            
            client = Neo4jClient()
            with pytest.raises(ValueError) as exc_info:
                await client.connect()
            
            assert "default" in str(exc_info.value).lower() or "not allowed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_connect_with_empty_password_raises_error(self):
        """Test that connecting with empty password raises ValueError."""
        settings = Neo4jSettings(
            uri="bolt://localhost:7687",
            user="neo4j",
            password=""
        )
        
        with patch("graph_db.neo4j_client.get_settings") as mock_get_settings:
            mock_get_settings.return_value.neo4j = settings
            
            client = Neo4jClient()
            with pytest.raises(ValueError) as exc_info:
                await client.connect()
            
            assert "must be set" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_connect_with_missing_uri_raises_error(self):
        """Test that connecting with missing URI raises ValueError."""
        settings = Neo4jSettings(
            uri="",
            user="neo4j",
            password="realpassword"
        )
        
        with patch("graph_db.neo4j_client.get_settings") as mock_get_settings:
            mock_get_settings.return_value.neo4j = settings
            
            client = Neo4jClient()
            with pytest.raises(ValueError) as exc_info:
                await client.connect()
            
            assert "uri" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_connect_with_missing_user_raises_error(self):
        """Test that connecting with missing user raises ValueError."""
        settings = Neo4jSettings(
            uri="bolt://localhost:7687",
            user="",
            password="realpassword"
        )
        
        with patch("graph_db.neo4j_client.get_settings") as mock_get_settings:
            mock_get_settings.return_value.neo4j = settings
            
            client = Neo4jClient()
            with pytest.raises(ValueError) as exc_info:
                await client.connect()
            
            assert "user" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_connect_with_valid_credentials_succeeds(self, mock_driver):
        """Test that connecting with valid credentials succeeds."""
        settings = Neo4jSettings(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="realpassword"
        )
        
        with patch("graph_db.neo4j_client.get_settings") as mock_get_settings, \
             patch("graph_db.neo4j_client.AsyncGraphDatabase.driver") as mock_create_driver:
            mock_get_settings.return_value.neo4j = settings
            mock_create_driver.return_value = mock_driver
            
            client = Neo4jClient()
            await client.connect()
            
            mock_driver.verify_connectivity.assert_called_once()
            mock_driver.session.assert_called_once_with(database="neo4j")

    @pytest.mark.asyncio
    async def test_connect_with_auth_failure_raises_clear_error(self, mock_driver):
        """Test that authentication failures raise clear error messages."""
        settings = Neo4jSettings(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="wrongpassword"
        )
        
        async def raise_auth_error():
            raise Exception("Authentication failed for user 'neo4j'")
        
        mock_driver.verify_connectivity = AsyncMock(side_effect=raise_auth_error)
        
        with patch("graph_db.neo4j_client.get_settings") as mock_get_settings, \
             patch("graph_db.neo4j_client.AsyncGraphDatabase.driver") as mock_create_driver:
            mock_get_settings.return_value.neo4j = settings
            mock_create_driver.return_value = mock_driver
            
            client = Neo4jClient()
            with pytest.raises(ValueError) as exc_info:
                await client.connect()
            
            assert "authentication" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_connect_on_auth_failure_closes_driver(self, mock_driver):
        """Test that the driver is closed on authentication failure."""
        settings = Neo4jSettings(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="wrongpassword"
        )
        
        async def raise_auth_error():
            raise Exception("Unauthorized access")
        
        mock_driver.verify_connectivity = AsyncMock(side_effect=raise_auth_error)
        
        with patch("graph_db.neo4j_client.get_settings") as mock_get_settings, \
             patch("graph_db.neo4j_client.AsyncGraphDatabase.driver") as mock_create_driver:
            mock_get_settings.return_value.neo4j = settings
            mock_create_driver.return_value = mock_driver
            
            client = Neo4jClient()
            with pytest.raises(Exception):
                await client.connect()
            
            mock_driver.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_connect_calls_reuse_driver(self, mock_driver):
        """Test that multiple connect calls reuse the same driver."""
        settings = Neo4jSettings(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="realpassword"
        )
        
        with patch("graph_db.neo4j_client.get_settings") as mock_get_settings, \
             patch("graph_db.neo4j_client.AsyncGraphDatabase.driver") as mock_create_driver:
            mock_get_settings.return_value.neo4j = settings
            mock_create_driver.return_value = mock_driver
            
            client = Neo4jClient()
            await client.connect()
            await client.connect()  # Second call
            
            mock_create_driver.assert_called_once()
