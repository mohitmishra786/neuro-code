"""Domain models with inheritance for graph exploration."""

from __future__ import annotations


class User:
    """A regular application user."""

    def __init__(self, name: str, email: str) -> None:
        self.name = name
        self.email = email

    def display_name(self) -> str:
        """Return a human-readable name."""
        return self.name

    def is_active(self) -> bool:
        return True


class AdminUser(User):
    """Administrator with elevated privileges."""

    def __init__(self, name: str, email: str, role: str = "admin") -> None:
        super().__init__(name, email)
        self.role = role

    def can_manage(self, user: User) -> bool:
        """Return True if this admin can manage ``user``."""
        return user.email != self.email

    def display_name(self) -> str:
        return f"{self.name} ({self.role})"
