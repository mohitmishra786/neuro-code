"""Application core wiring models and utils."""

from __future__ import annotations

from demo_pkg.models import AdminUser, User
from demo_pkg.utils.formatting import format_email, slugify


class Application:
    """Simple app container that registers users."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._users: list[User] = []

    def register(self, user: User) -> None:
        """Register a user."""
        self._users.append(user)

    def create_guest(self, name: str) -> User:
        """Create and register a guest user."""
        email = format_email(slugify(name), "example.com")
        user = User(name=name, email=email)
        self.register(user)
        return user

    def create_admin(self, name: str) -> AdminUser:
        """Create and register an admin user."""
        email = format_email(slugify(name), "example.com")
        admin = AdminUser(name=name, email=email)
        self.register(admin)
        return admin

    def user_count(self) -> int:
        return len(self._users)


def run_app(name: str = "demo") -> Application:
    """Bootstrap a demo application with sample users."""
    app = Application(name)
    app.create_guest("Alice")
    app.create_admin("Bob")
    return app
