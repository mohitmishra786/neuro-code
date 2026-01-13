"""
NeuroCode Query Library.

Optimized Cypher queries for common graph operations.
Requires Python 3.11+.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CypherQuery:
    """A named Cypher query with description."""

    name: str
    description: str
    query: str
    parameters: tuple[str, ...]


class QueryLibrary:
    """
    Library of optimized Cypher queries.

    All queries are designed for sub-50ms execution with proper indexes.
    """

    # Root and navigation queries

    GET_ROOT_MODULES = CypherQuery(
        name="get_root_modules",
        description="Get all top-level modules with child counts",
        query="""
        MATCH (m:Module)
        OPTIONAL MATCH (m)-[:CONTAINS]->(child)
        WITH m, count(child) as child_count
        RETURN m.id as id,
               m.name as name,
               m.path as path,
               m.qualified_name as qualified_name,
               m.lines_of_code as lines_of_code,
               m.docstring as docstring,
               child_count,
               'module' as type
        ORDER BY m.name
        """,
        parameters=(),
    )

    GET_NODE_BY_ID = CypherQuery(
        name="get_node_by_id",
        description="Get a single node by ID with all properties",
        query="""
        MATCH (n {id: $node_id})
        WITH n, labels(n) as labels
        OPTIONAL MATCH (n)-[:CONTAINS]->(child)
        WITH n, labels, count(child) as child_count
        OPTIONAL MATCH (parent)-[:CONTAINS]->(n)
        RETURN properties(n) as props,
               labels,
               child_count,
               parent.id as parent_id
        """,
        parameters=("node_id",),
    )

    GET_CHILDREN = CypherQuery(
        name="get_children",
        description="Get immediate children of a node ordered by type and line",
        query="""
        MATCH (parent {id: $node_id})-[:CONTAINS]->(child)
        OPTIONAL MATCH (child)-[:CONTAINS]->(grandchild)
        WITH child, labels(child) as labels, count(grandchild) as child_count
        RETURN child.id as id,
               child.name as name,
               child.qualified_name as qualified_name,
               child.line_number as line_number,
               child.docstring as docstring,
               child_count,
               labels,
               CASE
                   WHEN 'Module' IN labels THEN 'module'
                   WHEN 'Class' IN labels THEN 'class'
                   WHEN 'Function' IN labels THEN 'function'
                   WHEN 'Variable' IN labels THEN 'variable'
                   ELSE 'unknown'
               END as type,
               child.is_async as is_async,
               child.is_method as is_method,
               child.is_abstract as is_abstract,
               child.complexity as complexity,
               child.return_type as return_type,
               child.type_hint as type_hint
        ORDER BY
            CASE
                WHEN 'Class' IN labels THEN 0
                WHEN 'Function' IN labels THEN 1
                WHEN 'Variable' IN labels THEN 2
                ELSE 3
            END,
            child.line_number
        LIMIT $limit
        """,
        parameters=("node_id", "limit"),
    )

    GET_ANCESTORS = CypherQuery(
        name="get_ancestors",
        description="Get path from root to node (breadcrumbs)",
        query="""
        MATCH path = (root)-[:CONTAINS*0..]->(node {id: $node_id})
        WHERE NOT ()-[:CONTAINS]->(root)
        WITH nodes(path) as ancestors
        UNWIND range(0, size(ancestors)-1) as idx
        WITH ancestors[idx] as ancestor, idx, labels(ancestors[idx]) as labels
        RETURN ancestor.id as id,
               ancestor.name as name,
               ancestor.qualified_name as qualified_name,
               idx as depth,
               CASE
                   WHEN 'Module' IN labels THEN 'module'
                   WHEN 'Class' IN labels THEN 'class'
                   WHEN 'Function' IN labels THEN 'function'
                   ELSE 'unknown'
               END as type
        ORDER BY idx
        """,
        parameters=("node_id",),
    )

    # Search queries

    SEARCH_FULLTEXT = CypherQuery(
        name="search_fulltext",
        description="Full-text search across node names",
        query="""
        CALL db.index.fulltext.queryNodes('node_name_search', $search_text)
        YIELD node, score
        WITH node, score, labels(node) as labels
        WHERE score > 0.1
        RETURN node.id as id,
               node.name as name,
               node.qualified_name as qualified_name,
               node.line_number as line_number,
               node.docstring as docstring,
               score,
               CASE
                   WHEN 'Module' IN labels THEN 'module'
                   WHEN 'Class' IN labels THEN 'class'
                   WHEN 'Function' IN labels THEN 'function'
                   WHEN 'Variable' IN labels THEN 'variable'
                   ELSE 'unknown'
               END as type
        ORDER BY score DESC
        LIMIT $limit
        """,
        parameters=("search_text", "limit"),
    )

    SEARCH_EXACT_NAME = CypherQuery(
        name="search_exact_name",
        description="Search for exact node name match",
        query="""
        MATCH (n)
        WHERE n.name = $name
        WITH n, labels(n) as labels
        RETURN n.id as id,
               n.name as name,
               n.qualified_name as qualified_name,
               CASE
                   WHEN 'Module' IN labels THEN 'module'
                   WHEN 'Class' IN labels THEN 'class'
                   WHEN 'Function' IN labels THEN 'function'
                   WHEN 'Variable' IN labels THEN 'variable'
                   ELSE 'unknown'
               END as type
        LIMIT $limit
        """,
        parameters=("name", "limit"),
    )

    # Relationship queries

    GET_REFERENCES = CypherQuery(
        name="get_references",
        description="Get all nodes referencing or referenced by a node",
        query="""
        MATCH (node {id: $node_id})-[r]-(related)
        WHERE NOT type(r) = 'CONTAINS'
        WITH related, type(r) as rel_type, labels(related) as labels,
             CASE WHEN startNode(r) = node THEN 'outgoing' ELSE 'incoming' END as direction,
             properties(r) as rel_props
        RETURN related.id as id,
               related.name as name,
               related.qualified_name as qualified_name,
               related.line_number as line_number,
               rel_type,
               direction,
               rel_props,
               CASE
                   WHEN 'Module' IN labels THEN 'module'
                   WHEN 'Class' IN labels THEN 'class'
                   WHEN 'Function' IN labels THEN 'function'
                   WHEN 'Variable' IN labels THEN 'variable'
                   ELSE 'unknown'
               END as type
        ORDER BY rel_type, direction, related.name
        """,
        parameters=("node_id",),
    )

    GET_CALLERS = CypherQuery(
        name="get_callers",
        description="Get all functions that call a given function",
        query="""
        MATCH (caller:Function)-[r:CALLS]->(callee:Function {id: $node_id})
        RETURN caller.id as id,
               caller.name as name,
               caller.qualified_name as qualified_name,
               caller.line_number as line_number,
               r.call_count as call_count
        ORDER BY r.call_count DESC, caller.name
        """,
        parameters=("node_id",),
    )

    GET_CALLEES = CypherQuery(
        name="get_callees",
        description="Get all functions called by a given function",
        query="""
        MATCH (caller:Function {id: $node_id})-[r:CALLS]->(callee:Function)
        RETURN callee.id as id,
               callee.name as name,
               callee.qualified_name as qualified_name,
               callee.line_number as line_number,
               r.call_count as call_count
        ORDER BY r.call_count DESC, callee.name
        """,
        parameters=("node_id",),
    )

    GET_INHERITANCE_TREE = CypherQuery(
        name="get_inheritance_tree",
        description="Get class inheritance hierarchy",
        query="""
        MATCH path = (cls:Class {id: $node_id})-[:INHERITS*0..10]->(base:Class)
        UNWIND nodes(path) as node
        WITH DISTINCT node
        OPTIONAL MATCH (child:Class)-[:INHERITS]->(node)
        RETURN node.id as id,
               node.name as name,
               node.qualified_name as qualified_name,
               node.is_abstract as is_abstract,
               collect(DISTINCT child.id) as subclasses
        """,
        parameters=("node_id",),
    )

    # Statistics and analytics

    GET_MODULE_STATS = CypherQuery(
        name="get_module_stats",
        description="Get statistics for a module",
        query="""
        MATCH (m:Module {id: $node_id})
        OPTIONAL MATCH (m)-[:CONTAINS*]->(cls:Class)
        OPTIONAL MATCH (m)-[:CONTAINS*]->(func:Function)
        OPTIONAL MATCH (m)-[:CONTAINS*]->(var:Variable)
        RETURN m.lines_of_code as lines_of_code,
               count(DISTINCT cls) as class_count,
               count(DISTINCT func) as function_count,
               count(DISTINCT var) as variable_count
        """,
        parameters=("node_id",),
    )

    GET_COMPLEXITY_HOTSPOTS = CypherQuery(
        name="get_complexity_hotspots",
        description="Get functions with highest complexity",
        query="""
        MATCH (f:Function)
        WHERE f.complexity > 5
        RETURN f.id as id,
               f.name as name,
               f.qualified_name as qualified_name,
               f.complexity as complexity,
               f.line_number as line_number
        ORDER BY f.complexity DESC
        LIMIT $limit
        """,
        parameters=("limit",),
    )

    # Update queries

    UPDATE_NODE_HASH = CypherQuery(
        name="update_node_hash",
        description="Update the Merkle hash of a node",
        query="""
        MATCH (n {id: $node_id})
        SET n.hash = $hash
        RETURN n.id as id
        """,
        parameters=("node_id", "hash"),
    )

    DELETE_MODULE_CASCADE = CypherQuery(
        name="delete_module_cascade",
        description="Delete a module and all descendants",
        query="""
        MATCH (m:Module {path: $path})
        OPTIONAL MATCH (m)-[:CONTAINS*]->(descendant)
        WITH m, collect(descendant) as descendants
        UNWIND [m] + descendants as node
        DETACH DELETE node
        RETURN count(*) as deleted_count
        """,
        parameters=("path",),
    )

    # Batch operations

    BATCH_CREATE_CONTAINS = CypherQuery(
        name="batch_create_contains",
        description="Batch create CONTAINS relationships",
        query="""
        UNWIND $relationships as rel
        MATCH (parent {id: rel.parent_id})
        MATCH (child {id: rel.child_id})
        MERGE (parent)-[r:CONTAINS]->(child)
        SET r.weight = coalesce(rel.weight, 1)
        """,
        parameters=("relationships",),
    )

    BATCH_CREATE_CALLS = CypherQuery(
        name="batch_create_calls",
        description="Batch create CALLS relationships",
        query="""
        UNWIND $relationships as rel
        MATCH (caller:Function {id: rel.caller_id})
        MATCH (callee:Function {id: rel.callee_id})
        MERGE (caller)-[r:CALLS]->(callee)
        SET r.call_count = coalesce(r.call_count, 0) + rel.count
        """,
        parameters=("relationships",),
    )

    @classmethod
    def get_all_queries(cls) -> dict[str, CypherQuery]:
        """Get all queries as a dictionary."""
        return {
            name: getattr(cls, name)
            for name in dir(cls)
            if isinstance(getattr(cls, name), CypherQuery)
        }

    @classmethod
    def validate_parameters(
        cls, query: CypherQuery, params: dict[str, Any]
    ) -> list[str]:
        """Validate that all required parameters are provided."""
        missing = [p for p in query.parameters if p not in params]
        return missing
