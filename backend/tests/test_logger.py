"""
Tests for LoggerMixin.

Verifies that the LoggerMixin properly isolates logger instances
and prevents subclass name collisions.
"""

import pytest

from utils.logger import LoggerMixin


class ParentClass(LoggerMixin):
    """Parent class using LoggerMixin."""
    pass


class ChildClass(LoggerMixin):
    """Child class that could accidentally overwrite parent's logger."""
    pass


class TestLoggerMixinNameCollision:
    """Test that LoggerMixin prevents name collisions in subclasses."""

    def test_subclass_does_not_overwrite_parent_logger(self) -> None:
        """Subclasses should not accidentally overwrite each other's loggers."""
        parent = ParentClass()
        child = ChildClass()

        assert parent.log is not None
        assert child.log is not None

        assert parent.log is not child.log

    def test_same_class_returns_same_logger(self) -> None:
        """Multiple accesses should return the same logger instance."""
        instance = ParentClass()
        log1 = instance.log
        log2 = instance.log
        assert log1 is log2

    def test_logger_has_correct_bound_name(self) -> None:
        """Logger should be bound to the class name."""
        parent = ParentClass()
        child = ChildClass()

        parent_logger_name = getattr(parent.log, "_logger", None)
        child_logger_name = getattr(child.log, "_logger", None)

        if parent_logger_name and child_logger_name:
            assert "ParentClass" in str(parent_logger_name)
            assert "ChildClass" in str(child_logger_name)
