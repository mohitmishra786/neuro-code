"""
Tests for Logger performance optimizations.

Verifies that logging overhead is reduced through caching.
"""


import pytest


class TestLoggerOptimization:
    """Test cases for logger optimization."""

    def test_app_context_is_cached(self) -> None:
        """Test that app context cache dict is reused across calls."""
        import utils.logger as logger_mod

        # Direct assignment + function from module __dict__ (structlog may proxy attrs)
        logger_mod._app_context_cache = {
            "app": "CachedApp",
            "version": "9.9.9",
            "environment": "test",
        }
        get_ctx = logger_mod.__dict__.get("_get_app_context")
        if get_ctx is None:
            pytest.skip("_get_app_context not exposed on logger module")
        ctx = get_ctx()
        assert ctx["app"] == "CachedApp"
        assert get_ctx() is logger_mod._app_context_cache


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
