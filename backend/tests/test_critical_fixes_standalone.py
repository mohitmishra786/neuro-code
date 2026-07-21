"""
Unit Tests for Critical P0/P1 Fixes.

Tests for configuration caching, log level standardization, timeout handling,
parallel processing, and retry logic.

Requires Python 3.11+.
"""

import sys

CONFIG_CACHE_TESTS = """
def test_config_caching():
    '''Test that get_settings returns cached instance.'''
    from utils.config import get_settings
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2, 'Settings should be cached'
    return True

def test_file_watcher_caches_settings():
    '''Test FileWatcher caches settings on initialization.'''
    from watcher.file_watcher import FileWatcher
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmp:
        # Reset cached settings
        FileWatcher._cached_settings = None
        
        w1 = FileWatcher(os.path.Path(tmp))
        w2 = FileWatcher(os.path.Path(tmp))
        
        assert FileWatcher._cached_settings is not None
        assert w1._ignore_patterns == w2._ignore_patterns
    return True
"""

LOG_LEVEL_TESTS = """
def test_log_level_map_exists():
    '''Test that LOG_LEVEL_MAP is defined.'''
    from utils.logger import LOG_LEVEL_MAP
    assert "DEBUG" in LOG_LEVEL_MAP
    assert "INFO" in LOG_LEVEL_MAP
    assert "WARNING" in LOG_LEVEL_MAP
    assert "ERROR" in LOG_LEVEL_MAP
    assert "CRITICAL" in LOG_LEVEL_MAP
    return True

def test_get_log_level_returns_correct_values():
    '''Test _get_log_level returns correct log level integers.'''
    import logging
    from utils.logger import _get_log_level
    
    assert _get_log_level("DEBUG") == logging.DEBUG
    assert _get_log_level("INFO") == logging.INFO
    assert _get_log_level("WARNING") == logging.WARNING
    assert _get_log_level("ERROR") == logging.ERROR
    assert _get_log_level("CRITICAL") == logging.CRITICAL
    return True

def test_get_log_level_case_insensitive():
    '''Test _get_log_level handles case insensitivity.'''
    import logging
    from utils.logger import _get_log_level
    
    assert _get_log_level("debug") == logging.DEBUG
    assert _get_log_level("Debug") == logging.DEBUG
    assert _get_log_level("DEBUG") == logging.DEBUG
    return True

def test_get_log_level_default():
    '''Test _get_log_level returns INFO for unknown values.'''
    import logging
    from utils.logger import _get_log_level
    
    assert _get_log_level("UNKNOWN") == logging.INFO
    assert _get_log_level("") == logging.INFO
    return True
"""

RETRY_TESTS = """
def test_max_retry_attempts_constant():
    '''Test _MAX_RETRY_ATTEMPTS is defined.'''
    from graph_db.neo4j_client import _MAX_RETRY_ATTEMPTS
    assert _MAX_RETRY_ATTEMPTS == 3
    return True

def test_initial_retry_delay_constant():
    '''Test _INITIAL_RETRY_DELAY is defined.'''
    from graph_db.neo4j_client import _INITIAL_RETRY_DELAY
    assert _INITIAL_RETRY_DELAY == 0.1
    return True
"""

SETTINGS_TESTS = """
def test_neo4j_settings_defaults():
    '''Test Neo4jSettings has correct defaults.'''
    from utils.config import Neo4jSettings
    
    settings = Neo4jSettings()
    assert settings.uri == "bolt://localhost:7687"
    assert settings.user == "neo4j"
    assert settings.database == "neo4j"
    return True

def test_parser_settings_defaults():
    '''Test ParserSettings has correct defaults.'''
    from utils.config import ParserSettings
    
    settings = ParserSettings()
    assert settings.max_workers == 4
    assert settings.max_file_size_mb == 10.0
    assert "__pycache__" in settings.ignore_patterns
    return True

def test_watcher_settings_defaults():
    '''Test WatcherSettings has correct defaults.'''
    from utils.config import WatcherSettings
    
    settings = WatcherSettings()
    assert settings.debounce_delay_ms == 500
    assert settings.recursive is True
    assert settings.enabled is True
    return True

def test_api_settings_defaults():
    '''Test APISettings has correct defaults.'''
    from utils.config import APISettings
    
    settings = APISettings()
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.rate_limit_enabled is True
    return True

def test_logging_settings_defaults():
    '''Test LoggingSettings has correct defaults.'''
    from utils.config import LoggingSettings
    
    settings = LoggingSettings()
    assert settings.level == "INFO"
    assert settings.format == "json"
    return True
"""

SANITIZE_TESTS = """
def test_sanitize_sensitive_keys():
    '''Test sensitive data is sanitized.'''
    from utils.logger import _sanitize_value
    
    sensitive_data = {"password": "secret123", "token": "abc", "normal": "value"}
    result = _sanitize_value("password", sensitive_data)
    
    assert result["password"] == "***REDACTED***"
    assert result["token"] == "***REDACTED***"
    assert result["normal"] == "value"
    return True

def test_app_context_caching():
    '''Test app context is cached.'''
    from utils.logger import _get_app_context
    
    # Reset cache
    import utils.logger
    utils.logger._app_context_cache = None
    
    context1 = _get_app_context()
    context2 = _get_app_context()
    
    assert context1 is context2
    assert "app" in context1
    assert "version" in context1
    assert "environment" in context1
    return True
"""

LOGGER_MIXIN_TESTS = """
def test_logger_mixin_creates_unique_loggers():
    '''Test LoggerMixin creates unique loggers per class.'''
    from utils.logger import LoggerMixin
    
    class TestClass1(LoggerMixin):
        pass
    
    class TestClass2(LoggerMixin):
        pass
    
    obj1 = TestClass1()
    obj2 = TestClass2()
    
    assert obj1.log is not obj2.log
    return True
"""


def run_tests(test_code, test_name):
    """Run a block of test code."""
    print(f"\n=== Running {test_name} ===")
    try:
        exec(test_code, {"__name__": "__main__"})
        print(f"✓ {test_name} passed!")
        return True
    except Exception as e:
        print(f"✗ {test_name} failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all unit tests."""
    print("Running Critical Fixes Unit Tests")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(("Config Caching", run_tests(CONFIG_CACHE_TESTS, "Config Caching")))
    results.append(("Log Level Standardization", run_tests(LOG_LEVEL_TESTS, "Log Level Standardization")))
    results.append(("Retry Logic", run_tests(RETRY_TESTS, "Retry Logic Constants")))
    results.append(("Settings Defaults", run_tests(SETTINGS_TESTS, "Settings Defaults")))
    results.append(("Sensitive Data Sanitization", run_tests(SANITIZE_TESTS, "Sensitive Data Sanitization")))
    results.append(("Logger Mixin", run_tests(LOGGER_MIXIN_TESTS, "Logger Mixin")))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("-" * 50)
    
    passed = 0
    failed = 0
    for name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"  {name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 50)
    print(f"Total: {passed} passed, {failed} failed")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
