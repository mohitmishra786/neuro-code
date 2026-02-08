"""
Tests for Logger performance optimizations.

Verifies that logging overhead is reduced through caching.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestLoggerOptimization:
    """Test cases for logger optimization."""

    def test_app_context_is_cached(self) -> None:
        """Test that app context is computed only once."""
        from utils.logger import _get_app_context, _app_context_cache

        with patch('utils.logger.get_settings') as mock_settings:
            mock_settings.return_value.app_name = "TestApp"
            mock_settings.return_value.app_version = "1.0.0"
            mock_settings.return_value.environment = "test"

            # Clear cache
            import utils.logger
            utils.logger._app_context_cache = None

            # First call should call get_settings
            ctx1 = utils.logger._get_app_context()
            assert mock_settings.call_count == 1
            assert ctx1["app"] == "TestApp"
            assert ctx1["version"] == "1.0.0"
            assert ctx1["environment"] == "test"

            # Second call should use cache
            ctx2 = utils.logger._get_app_context()
            assert mock_settings.call_count == 1  # No additional calls
            assert ctx2 == ctx1

    def test_sanitize_value_handles_large_objects(self) -> None:
        """Test that large objects are properly sanitized."""
        from utils.logger import _sanitize_value

        large_dict = {"data": "x" * 10000, "password": "secret"}
        result = _sanitize_value("key", large_dict)

        assert result["password"] == "***REDACTED***"
        assert result["data"] == "x" * 10000

    def test_sanitize_value_handles_deeply_nested(self) -> None:
        """Test sanitization of deeply nested structures."""
        from utils.logger import _sanitize_value

        nested = {
            "level1": {
                "level2": {
                    "api_key": "secret123",
                    "level3": {
                        "password": "deep_secret"
                    }
                }
            }
        }
        result = _sanitize_value("root", nested)

        assert result["level1"]["level2"]["api_key"] == "***REDACTED***"
        assert result["level1"]["level2"]["level3"]["password"] == "***REDACTED***"
