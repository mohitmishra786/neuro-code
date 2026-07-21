"""Service layer calling into the application core."""

from __future__ import annotations

from demo_pkg.core import Application, run_app
from demo_pkg.models import User


class UserService:
    """High-level user operations."""

    def __init__(self, app: Application | None = None) -> None:
        self.app = app or run_app()

    def list_names(self) -> list[str]:
        """Return display names for all registered users."""
        return [u.display_name() for u in self.app._users]

    def ensure_user(self, name: str) -> User:
        """Create a guest if needed and return them."""
        return self.app.create_guest(name)
