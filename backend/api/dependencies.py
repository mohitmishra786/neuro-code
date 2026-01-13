"""
NeuroCode API Dependencies.

Shared dependencies for FastAPI routes.
Requires Python 3.11+.
"""

from typing import Any

from fastapi import HTTPException

from graph_db.neo4j_client import Neo4jClient


# Shared state - populated by main.py lifespan
_state: dict[str, Any] = {}


def set_neo4j_client(client: Neo4jClient | None) -> None:
    """Set the shared Neo4j client instance."""
    _state["neo4j_client"] = client


def get_neo4j_client() -> Neo4jClient | None:
    """Get the shared Neo4j client instance."""
    return _state.get("neo4j_client")


def require_neo4j_client() -> Neo4jClient:
    """
    Dependency that requires a Neo4j client.
    
    Raises HTTPException if client is unavailable.
    """
    client = get_neo4j_client()
    if client is None:
        raise HTTPException(
            status_code=503,
            detail="Database connection unavailable",
        )
    return client
