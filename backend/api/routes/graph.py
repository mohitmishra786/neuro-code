"""
NeuroCode Graph API Routes.

REST endpoints for graph operations.
Requires Python 3.11+.
"""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from api.dependencies import require_neo4j_client
from graph_db.neo4j_client import Neo4jClient
from parser.tree_sitter_parser import TreeSitterParser
from parser.relationship_extractor import RelationshipExtractor
from merkle.change_detector import ChangeDetector
from utils.logger import get_logger

router = APIRouter()
logger = get_logger("api.graph")

# Shared state for parser and change detector
_parser = TreeSitterParser()
_change_detector = ChangeDetector()
_relationship_extractor = RelationshipExtractor()


class NodeResponse(BaseModel):
    """Response model for a graph node."""

    id: str
    name: str
    type: str
    qualified_name: str | None = None
    line_number: int | None = None
    docstring: str | None = None
    child_count: int = 0
    is_async: bool | None = None
    is_method: bool | None = None
    is_abstract: bool | None = None
    complexity: int | None = None
    return_type: str | None = None
    type_hint: str | None = None


class RootNodesResponse(BaseModel):
    """Response model for root nodes."""

    nodes: list[NodeResponse]
    total: int


class ChildrenResponse(BaseModel):
    """Response model for node children."""

    parent_id: str
    children: list[NodeResponse]
    total: int


class AncestorsResponse(BaseModel):
    """Response model for node ancestors."""

    node_id: str
    ancestors: list[NodeResponse]


class ReferenceNode(BaseModel):
    """Node with relationship information."""

    id: str
    name: str
    type: str
    qualified_name: str | None = None
    relationship_type: str
    direction: str
    line_number: int | None = None


class ReferencesResponse(BaseModel):
    """Response model for node references."""

    node_id: str
    references: list[ReferenceNode]
    total: int


class ParseRequest(BaseModel):
    """Request model for parsing a codebase."""

    path: str = Field(..., description="Path to the Python codebase to parse")
    recursive: bool = Field(default=True, description="Parse subdirectories recursively")


class ParseResponse(BaseModel):
    """Response model for parse operation."""

    status: str
    modules_parsed: int = 0
    relationships_created: int = 0
    errors: list[str] = []


class UpdateRequest(BaseModel):
    """Request model for updating changed files."""

    paths: list[str] = Field(..., description="List of changed file paths")


class UpdateResponse(BaseModel):
    """Response model for update operation."""

    status: str
    files_updated: int = 0
    nodes_added: int = 0
    nodes_modified: int = 0
    nodes_removed: int = 0



# Use require_neo4j_client directly as dependency
get_client = require_neo4j_client



@router.get("/root", response_model=RootNodesResponse)
async def get_root_nodes(
    client: Neo4jClient = Depends(get_client),
) -> RootNodesResponse:
    """
    Get all root-level modules.

    Returns top-level modules with child counts for initial graph display.
    Target latency: <100ms
    """
    logger.debug("fetching_root_nodes")

    try:
        results = await client.get_root_nodes()
        nodes = [
            NodeResponse(
                id=r["id"],
                name=r["name"],
                type=r["type"],
                qualified_name=r.get("qualified_name"),
                docstring=r.get("docstring"),
                child_count=r.get("child_count", 0),
            )
            for r in results
        ]
        return RootNodesResponse(nodes=nodes, total=len(nodes))

    except Exception as e:
        logger.error("get_root_nodes_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/node/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: str,
    client: Neo4jClient = Depends(get_client),
) -> NodeResponse:
    """
    Get a single node by ID.

    Returns full node details.
    Target latency: <50ms
    """
    logger.debug("fetching_node", node_id=node_id)

    try:
        result = await client.get_node_by_id(node_id)
        if not result:
            raise HTTPException(status_code=404, detail="Node not found")

        labels = result.get("labels", [])
        node_type = "unknown"
        if "Module" in labels:
            node_type = "module"
        elif "Class" in labels:
            node_type = "class"
        elif "Function" in labels:
            node_type = "function"
        elif "Variable" in labels:
            node_type = "variable"

        return NodeResponse(
            id=result["id"],
            name=result.get("name", ""),
            type=node_type,
            qualified_name=result.get("qualified_name"),
            line_number=result.get("line_number"),
            docstring=result.get("docstring"),
            child_count=result.get("child_count", 0),
            is_async=result.get("is_async"),
            is_method=result.get("is_method"),
            is_abstract=result.get("is_abstract"),
            complexity=result.get("complexity"),
            return_type=result.get("return_type"),
            type_hint=result.get("type_hint"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_node_failed", node_id=node_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/node/{node_id}/children", response_model=ChildrenResponse)
async def get_node_children(
    node_id: str,
    limit: int = Query(default=1000, ge=1, le=5000),
    client: Neo4jClient = Depends(get_client),
) -> ChildrenResponse:
    """
    Get immediate children of a node.

    Returns children ordered by type (classes first, then functions, then variables)
    and by line number within each type.
    Target latency: <50ms
    """
    logger.debug("fetching_children", node_id=node_id, limit=limit)

    try:
        results = await client.get_node_children(node_id)
        children = [
            NodeResponse(
                id=r["id"],
                name=r["name"],
                type=r["type"],
                qualified_name=r.get("qualified_name"),
                line_number=r.get("line_number"),
                docstring=r.get("docstring"),
                child_count=r.get("child_count", 0),
                is_async=r.get("is_async"),
                is_method=r.get("is_method"),
                is_abstract=r.get("is_abstract"),
                complexity=r.get("complexity"),
            )
            for r in results[:limit]
        ]
        return ChildrenResponse(
            parent_id=node_id,
            children=children,
            total=len(children),
        )

    except Exception as e:
        logger.error("get_children_failed", node_id=node_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/node/{node_id}/ancestors", response_model=AncestorsResponse)
async def get_node_ancestors(
    node_id: str,
    client: Neo4jClient = Depends(get_client),
) -> AncestorsResponse:
    """
    Get path from root to node (for breadcrumbs).

    Returns ordered list of ancestors from root to parent.
    Target latency: <30ms
    """
    logger.debug("fetching_ancestors", node_id=node_id)

    try:
        results = await client.get_node_ancestors(node_id)
        ancestors = [
            NodeResponse(
                id=r["id"],
                name=r["name"],
                type=r["type"],
                qualified_name=r.get("qualified_name"),
            )
            for r in results
        ]
        return AncestorsResponse(node_id=node_id, ancestors=ancestors)

    except Exception as e:
        logger.error("get_ancestors_failed", node_id=node_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/node/{node_id}/references", response_model=ReferencesResponse)
async def get_node_references(
    node_id: str,
    client: Neo4jClient = Depends(get_client),
) -> ReferencesResponse:
    """
    Get all nodes that reference or are referenced by this node.

    Excludes CONTAINS relationships (use /children for those).
    Target latency: <100ms
    """
    logger.debug("fetching_references", node_id=node_id)

    try:
        results = await client.get_node_references(node_id)
        references = [
            ReferenceNode(
                id=r["id"],
                name=r["name"],
                type=r["type"],
                qualified_name=r.get("qualified_name"),
                relationship_type=r["rel_type"],
                direction=r["direction"],
                line_number=r.get("line_number"),
            )
            for r in results
        ]
        return ReferencesResponse(
            node_id=node_id,
            references=references,
            total=len(references),
        )

    except Exception as e:
        logger.error("get_references_failed", node_id=node_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse", response_model=ParseResponse)
async def parse_codebase(
    request: ParseRequest,
    background_tasks: BackgroundTasks,
    client: Neo4jClient = Depends(get_client),
) -> ParseResponse:
    """
    Parse a Python codebase and populate the graph.

    This is an async operation that runs in the background.
    Large codebases may take several seconds to parse.
    """
    logger.info("parse_requested", path=request.path)

    codebase_path = Path(request.path)
    if not codebase_path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {request.path}")

    if not codebase_path.is_dir():
        raise HTTPException(status_code=400, detail="Path must be a directory")

    # Find all Python files
    if request.recursive:
        python_files = list(codebase_path.rglob("*.py"))
    else:
        python_files = list(codebase_path.glob("*.py"))

    # Filter out ignored patterns
    from utils.config import get_settings
    settings = get_settings()
    ignore_patterns = settings.parser.ignore_patterns

    def should_ignore(path: Path) -> bool:
        path_str = str(path)
        for pattern in ignore_patterns:
            if pattern in path_str:
                return True
        return False

    python_files = [f for f in python_files if not should_ignore(f)]

    if not python_files:
        return ParseResponse(
            status="completed",
            modules_parsed=0,
            errors=["No Python files found"],
        )

    # Parse all files
    modules = []
    errors = []

    for file_path in python_files:
        try:
            module = _parser.parse_file(file_path)
            modules.append(module)
        except Exception as e:
            errors.append(f"{file_path}: {e}")

    if not modules:
        return ParseResponse(
            status="failed",
            modules_parsed=0,
            errors=errors,
        )

    # Extract relationships
    relationships = _relationship_extractor.extract_relationships(modules)

    # Store in Neo4j
    try:
        # Clear existing data (optional - could be made configurable)
        # await client.clear_database()

        nodes_created = await client.bulk_create_nodes(modules)
        rels_created = await client.bulk_create_relationships(relationships)

        # Initialize change detector cache
        _change_detector.initialize_from_modules(modules)

        logger.info(
            "parse_completed",
            modules=len(modules),
            nodes=nodes_created,
            relationships=rels_created,
        )

        return ParseResponse(
            status="completed",
            modules_parsed=len(modules),
            relationships_created=rels_created,
            errors=errors,
        )

    except Exception as e:
        logger.error("parse_storage_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update", response_model=UpdateResponse)
async def update_changed_files(
    request: UpdateRequest,
    client: Neo4jClient = Depends(get_client),
) -> UpdateResponse:
    """
    Update the graph for changed files.

    Performs incremental update using Merkle tree change detection.
    Target latency: <1s for single file
    """
    logger.info("update_requested", file_count=len(request.paths))

    paths = [Path(p) for p in request.paths]
    changes = _change_detector.detect_changes_batch(paths)

    if not changes.has_changes:
        return UpdateResponse(status="no_changes", files_updated=len(paths))

    try:
        # Get updated modules
        updated_modules = [
            _change_detector.get_module(Path(p))
            for p in changes.affected_modules
            if _change_detector.get_module(Path(p))
        ]

        # Delete removed nodes
        for removed in changes.removed_nodes:
            # Find the module path and delete
            for path_str in changes.affected_modules:
                path = Path(path_str)
                if path.exists():
                    await client.delete_module(str(path))
                    break

        # Create/update nodes
        nodes_created = 0
        if updated_modules:
            nodes_created = await client.bulk_create_nodes(updated_modules)

            # Re-extract and create relationships
            relationships = _relationship_extractor.extract_relationships(updated_modules)
            await client.bulk_create_relationships(relationships)

        return UpdateResponse(
            status="completed",
            files_updated=len(request.paths),
            nodes_added=len(changes.added_nodes),
            nodes_modified=len(changes.modified_nodes),
            nodes_removed=len(changes.removed_nodes),
        )

    except Exception as e:
        logger.error("update_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_graph(
    client: Neo4jClient = Depends(get_client),
) -> dict[str, str]:
    """
    Clear all nodes and relationships from the graph.

    WARNING: This is destructive and cannot be undone.
    """
    logger.warning("clear_graph_requested")

    try:
        await client.clear_database()
        _change_detector.clear_cache()
        return {"status": "cleared"}

    except Exception as e:
        logger.error("clear_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
