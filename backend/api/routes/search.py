"""
NeuroCode Search API Routes.

Search endpoints for the graph.
Requires Python 3.11+.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.dependencies import require_neo4j_client
from graph_db.neo4j_client import Neo4jClient
from utils.logger import get_logger

router = APIRouter()
logger = get_logger("api.search")


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


@router.get("", response_model=SearchResponse)
async def search_nodes(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum results"),
    type_filter: str | None = Query(
        default=None,
        description="Filter by node type (module, class, function, variable)",
    ),
    client: Neo4jClient = Depends(require_neo4j_client),
) -> SearchResponse:
    """
    Full-text search across all node names.

    Uses fuzzy matching to find nodes by name or qualified name.
    Target latency: <200ms
    """
    logger.debug("search_requested", query=q, limit=limit, type_filter=type_filter)

    try:
        results = await client.search_nodes(q, limit=limit * 2)  # Fetch extra for filtering

        # Filter by type if specified
        if type_filter:
            type_filter = type_filter.lower()
            results = [r for r in results if r.get("type") == type_filter]

        # Limit results
        results = results[:limit]

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
            query=q,
            results=search_results,
            total=len(search_results),
        )

    except Exception as e:
        logger.error("search_failed", query=q, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


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
