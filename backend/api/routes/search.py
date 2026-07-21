"""
NeuroCode Search API Routes.

Search endpoints for graph with validation and security.
Requires Python 3.11+.
"""

import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ValidationError, field_validator

from api.dependencies import require_neo4j_client
from graph_db.neo4j_client import Neo4jClient
from utils.logger import get_logger

router = APIRouter()
logger = get_logger("api.search")


class SearchQuery(BaseModel):
    """Validated search query model."""

    query: str
    limit: int = 50
    type_filter: str | None = None

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """
        Validate and sanitize search query.

        - Must not be empty
        - Must be reasonable length
        - Must not contain suspicious patterns
        """
        if not v or not v.strip():
            raise ValueError("Search query cannot be empty")
        
        v = v.strip()
        
        if len(v) > 100:
            raise ValueError("Search query too long (max 100 characters)")
        
        # Check for injection patterns (very basic, Neo4j query injection is the main concern)
        injection_patterns = [
            r';.*DROP',
            r';.*DELETE',
            r';.*INSERT',
            r';.*MERGE',
            r';.*CREATE',
            r'union.*select',
            r'--',
            r'/\*.*\*/',
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Invalid search query pattern detected")
        
        return v


class SearchResult(BaseModel):
    """A single search result."""

    id: str
    name: str
    type: str
    qualified_name: str | None = None
    line_number: int | None = None
    docstring: str | None = None
    score: float


class SearchResponse(BaseModel):
    """Response model for search."""

    query: str
    results: list[SearchResult]
    total: int


async def _run_search(
    request: SearchQuery,
    client: Neo4jClient,
) -> SearchResponse:
    """Shared search implementation for GET and POST."""
    logger.debug(
        "search_requested",
        query=request.query,
        limit=request.limit,
        type_filter=request.type_filter,
    )

    try:
        escaped_query = request.query.replace("~", "\\~").replace("*", "\\*")
        results = await client.search_nodes(escaped_query, limit=request.limit * 2)

        if request.type_filter:
            type_filter = request.type_filter.lower()
            valid_types = {"module", "class", "function", "variable", "package"}
            if type_filter not in valid_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid type filter. Must be one of: {', '.join(sorted(valid_types))}",
                )
            results = [r for r in results if r.get("type") == type_filter]

        results = results[: request.limit]
        search_results = [
            SearchResult(
                id=r["id"],
                name=r["name"],
                type=r["type"],
                qualified_name=r.get("qualified_name"),
                line_number=r.get("line_number"),
                docstring=r.get("docstring"),
                score=r.get("score", 0.0),
            )
            for r in results
        ]

        return SearchResponse(
            query=request.query,
            results=search_results,
            total=len(search_results),
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("search_validation_failed", query=request.query, error=str(e))
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        logger.error("search_failed", query=request.query, error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("", response_model=SearchResponse)
async def search_nodes_get(
    q: str = Query(..., description="Search query"),
    limit: int = Query(default=50, ge=1, le=200),
    type_filter: str | None = Query(default=None),
    client: Neo4jClient = Depends(require_neo4j_client),
) -> SearchResponse:
    """
    Full-text search (GET). Query param ``q`` matches docs and frontend conventions.
    """
    try:
        request = SearchQuery(query=q, limit=limit, type_filter=type_filter)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()) from e
    return await _run_search(request, client)


@router.post("", response_model=SearchResponse)
async def search_nodes_post(
    request: SearchQuery,
    client: Neo4jClient = Depends(require_neo4j_client),
) -> SearchResponse:
    """Full-text search (POST body)."""
    return await _run_search(request, client)


@router.get("/suggest")
async def get_suggestions(
    q: str = Query(..., min_length=1, max_length=50, description="Partial query"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum suggestions"),
    client: Neo4jClient = Depends(require_neo4j_client),
) -> dict[str, Any]:
    """
    Get autocomplete suggestions for a partial query.

    Returns quick suggestions for search-as-you-type.
    Target latency: <100ms
    """
    logger.debug("suggestions_requested", query=q, limit=limit)

    try:
        # Use prefix search for suggestions
        results = await client.search_nodes(f"{q}*", limit=limit)

        suggestions = [
            {
                "name": r["name"],
                "qualified_name": r.get("qualified_name"),
                "type": r["type"],
            }
            for r in results
        ]

        return {
            "query": q,
            "suggestions": suggestions,
        }

    except Exception as e:
        logger.error("suggestions_failed", query=q, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def get_node_types(
    client: Neo4jClient = Depends(require_neo4j_client),
) -> dict[str, Any]:
    """
    Get counts of each node type in the graph.

    Useful for displaying filter options in the UI.
    """
    try:
        query = """
        MATCH (n)
        WITH labels(n) as labels
        UNWIND labels as label
        RETURN label, count(*) as count
        ORDER BY count DESC
        """
        results = await client.execute_query(query)

        type_counts = {r["label"].lower(): r["count"] for r in results}

        return {
            "types": type_counts,
            "total": sum(type_counts.values()),
        }

    except Exception as e:
        logger.error("get_types_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
