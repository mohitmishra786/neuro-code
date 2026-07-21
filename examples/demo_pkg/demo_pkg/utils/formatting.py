"""String formatting helpers."""

from __future__ import annotations


def format_email(local: str, domain: str) -> str:
    """Build an email address from parts."""
    return f"{local}@{domain}"


def slugify(text: str) -> str:
    """Convert text to a simple URL slug."""
    return "-".join(text.lower().split())
