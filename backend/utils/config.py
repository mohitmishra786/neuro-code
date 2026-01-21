"""
NeuroCode Configuration Module.

Centralizes all configuration settings using Pydantic Settings.
Requires Python 3.11+.
"""

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env file into os.environ at module import time
# This ensures nested BaseSettings classes can read the values
_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    load_dotenv(_env_file)
else:
    # Try current working directory
    load_dotenv()


class Neo4jSettings(BaseSettings):
    """Neo4j database connection settings."""

    model_config = SettingsConfigDict(env_prefix="NEO4J_")

    uri: str = Field(default="bolt://localhost:7687", description="Neo4j connection URI")
    user: str = Field(default="neo4j", description="Neo4j username")
    password: str = Field(default="password", description="Neo4j password")
    database: str = Field(default="neo4j", description="Neo4j database name")
    max_connection_pool_size: int = Field(default=50, ge=1, le=100)
    connection_timeout: float = Field(default=30.0, ge=1.0)


class ParserSettings(BaseSettings):
    """Parser configuration settings."""

    model_config = SettingsConfigDict(env_prefix="PARSER_")

    max_workers: int = Field(default=4, ge=1, le=32, description="Parallel parsing workers")
    max_file_size_mb: float = Field(default=10.0, ge=0.1, description="Max file size to parse")
    timeout_seconds: float = Field(default=30.0, ge=1.0, description="Parse timeout per file")

    ignore_patterns: list[str] = Field(
        default=[
            "*.pyc",
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            ".idea",
            ".vscode",
            "*.egg-info",
            "dist",
            "build",
            "node_modules",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
        ],
        description="Glob patterns to ignore during parsing",
    )

    @field_validator("ignore_patterns", mode="before")
    @classmethod
    def parse_ignore_patterns(cls, v: str | list[str]) -> list[str]:
        """Parse ignore patterns from comma-separated string or list."""
        if isinstance(v, str):
            return [p.strip() for p in v.split(",") if p.strip()]
        return v


class WatcherSettings(BaseSettings):
    """File watcher configuration settings."""

    model_config = SettingsConfigDict(env_prefix="WATCHER_")

    debounce_delay_ms: int = Field(default=500, ge=100, le=5000)
    recursive: bool = Field(default=True)
    enabled: bool = Field(default=True)


class APISettings(BaseSettings):
    """API server configuration settings."""

    model_config = SettingsConfigDict(env_prefix="API_")

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    debug: bool = Field(default=False)
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins",
    )
    request_timeout: float = Field(default=60.0, ge=1.0)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    model_config = SettingsConfigDict(env_prefix="LOG_")

    level: str = Field(default="INFO")
    format: str = Field(default="json")  # "json" or "console"
    file_path: Path | None = Field(default=None)


class Settings(BaseSettings):
    """Main application settings aggregating all sub-settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application metadata
    app_name: str = Field(default="NeuroCode")
    app_version: str = Field(default="0.1.0")
    environment: str = Field(default="development")

    # Sub-settings
    neo4j: Neo4jSettings = Field(default_factory=Neo4jSettings)
    parser: ParserSettings = Field(default_factory=ParserSettings)
    watcher: WatcherSettings = Field(default_factory=WatcherSettings)
    api: APISettings = Field(default_factory=APISettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() in ("development", "dev", "local")

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() in ("production", "prod")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get cached application settings.

    Returns singleton instance of Settings for performance.
    Use dependency injection in FastAPI routes.
    """
    return Settings()


# Type alias for dependency injection
SettingsDep = Annotated[Settings, Field(default_factory=get_settings)]
