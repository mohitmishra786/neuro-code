"""Tests for parse path allowlist enforcement (security R14)."""

from __future__ import annotations

from pathlib import Path

import pytest

from api.path_security import validate_parse_directory
from utils.config import get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_allows_path_under_allowlist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    monkeypatch.setenv("API_ALLOWED_PARSE_PATHS", str(tmp_path))
    get_settings.cache_clear()

    result = validate_parse_directory(str(project))
    assert Path(result) == project.resolve()


def test_rejects_outside_allowlist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.setenv("API_ALLOWED_PARSE_PATHS", str(allowed))
    get_settings.cache_clear()

    with pytest.raises(ValueError, match="allowed"):
        validate_parse_directory(str(outside))


def test_rejects_traversal_segments(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    monkeypatch.setenv("API_ALLOWED_PARSE_PATHS", str(allowed))
    get_settings.cache_clear()

    with pytest.raises(ValueError, match="traversal"):
        validate_parse_directory(str(allowed / ".." / "secret"))


def test_rejects_missing_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_ALLOWED_PARSE_PATHS", str(tmp_path))
    get_settings.cache_clear()

    with pytest.raises(ValueError, match="does not exist"):
        validate_parse_directory(str(tmp_path / "nope"))
