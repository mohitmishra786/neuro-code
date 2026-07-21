"""
Filesystem path security helpers for parse/update endpoints.
"""

from __future__ import annotations

from pathlib import Path

from utils.config import get_settings


def validate_parse_directory(path: str) -> str:
    """
    Validate a directory path for parse operations.

    - Rejects explicit ``..`` segments
    - Requires the path to exist and be a directory
    - Requires the path to be under ``API_ALLOWED_PARSE_PATHS``

    Returns:
        Resolved absolute path string.

    Raises:
        ValueError: If the path is invalid or not allowed.
    """
    parts = Path(path).parts
    if ".." in parts:
        raise ValueError("Path traversal not allowed")

    resolved = Path(path).expanduser().resolve()

    if not resolved.exists():
        raise ValueError(f"Path does not exist: {path}")

    if not resolved.is_dir():
        raise ValueError(f"Path must be a directory: {path}")

    settings = get_settings()
    allowed_raw = settings.api.allowed_parse_paths
    if not allowed_raw:
        raise ValueError("No allowed parse paths configured (API_ALLOWED_PARSE_PATHS)")

    allowed = [Path(p).expanduser().resolve() for p in allowed_raw]
    under_allowed = False
    for base in allowed:
        try:
            resolved.relative_to(base)
            under_allowed = True
            break
        except ValueError:
            continue
    if not under_allowed:
        raise ValueError(
            f"Path not in allowed directories: {path}. "
            f"Configure API_ALLOWED_PARSE_PATHS (defaults to cwd)."
        )

    return str(resolved)
