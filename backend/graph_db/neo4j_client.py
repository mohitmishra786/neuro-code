"""
NeuroCode Neo4j Client.

Async Neo4j driver wrapper with connection pooling and query caching.
Requires Python 3.11+.
"""

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncIterator
from uuid import UUID

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession, AsyncTransaction
from neo4j.exceptions import ServiceUnavailable, SessionExpired, TransientError

from graph_db.schema import GraphSchema, NodeLabel, RelationshipLabel
from parser.models import ModuleInfo, ClassInfo, FunctionInfo, VariableInfo, Relationship
from utils.config import get_settings
from utils.logger import LoggerMixin


class Neo4jClient(LoggerMixin):
    """
    Async Neo4j client with connection pooling and retry logic.

    Provides high-level methods for graph operations with
    automatic retry on transient failures.
    """

    def __init__(self) -> None:
        """Initialize the Neo4j client."""
        self._driver: AsyncDriver | None = None
        self._settings = get_settings().neo4j

    async def connect(self) -> None:
        """
        Establish connection to Neo4j.

        Creates an async driver with connection pooling.
        """
        if self._driver is not None:
            return

        self._driver = AsyncGraphDatabase.driver(
            self._settings.uri,
            auth=(self._settings.user, self._settings.password),
            max_connection_pool_size=self._settings.max_connection_pool_size,
            connection_timeout=self._settings.connection_timeout,
        )

        # Verify connectivity
        try:
            await self._driver.verify_connectivity()
            self.log.info(
                "neo4j_connected",
                uri=self._settings.uri,
                database=self._settings.database,
            )
        except Exception as e:
            self.log.error("neo4j_connection_failed", error=str(e))
            raise

    async def close(self) -> None:
        """Close the Neo4j connection."""
        if self._driver is not None:
            await self._driver.close()
            self._driver = None
            self.log.info("neo4j_disconnected")

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """
        Get a Neo4j session with automatic cleanup.

        Yields:
            AsyncSession for executing queries
        """
        if self._driver is None:
            await self.connect()

        assert self._driver is not None
        session = self._driver.session(database=self._settings.database)
        try:
            yield session
        finally:
            await session.close()

    async def execute_query(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        retries: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Execute a Cypher query with retry logic.

        Args:
            query: Cypher query string
            parameters: Query parameters
            retries: Number of retries on transient errors

        Returns:
            List of result records as dictionaries
        """
        last_error: Exception | None = None

        for attempt in range(retries):
            try:
                async with self.session() as session:
                    result = await session.run(query, parameters or {})
                    records = await result.data()
                    return records

            except (ServiceUnavailable, SessionExpired, TransientError) as e:
                last_error = e
                self.log.warning(
                    "query_retry",
                    attempt=attempt + 1,
                    error=str(e),
                )
                await asyncio.sleep(0.1 * (2**attempt))  # Exponential backoff

            except Exception as e:
                self.log.error("query_failed", query=query[:100], error=str(e))
                raise

        if last_error:
            raise last_error
        return []

    async def execute_write(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute a write query in a transaction.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            Summary of the write operation
        """
        async with self.session() as session:
            result = await session.run(query, parameters or {})
            summary = await result.consume()
            return {
                "nodes_created": summary.counters.nodes_created,
                "nodes_deleted": summary.counters.nodes_deleted,
                "relationships_created": summary.counters.relationships_created,
                "relationships_deleted": summary.counters.relationships_deleted,
                "properties_set": summary.counters.properties_set,
            }

    async def initialize_schema(self) -> None:
        """
        Initialize the graph schema with indexes and constraints.

        Safe to call multiple times (uses IF NOT EXISTS).
        """
        self.log.info("initializing_schema")

        # Create constraints
        for statement in GraphSchema.get_constraint_creation_statements():
            try:
                await self.execute_write(statement)
            except Exception as e:
                self.log.warning("constraint_creation_warning", statement=statement, error=str(e))

        # Create indexes
        for statement in GraphSchema.get_index_creation_statements():
            try:
                await self.execute_write(statement)
            except Exception as e:
                self.log.warning("index_creation_warning", statement=statement, error=str(e))

        self.log.info("schema_initialized")

    async def clear_database(self) -> None:
        """
        Clear all nodes and relationships from the database.

        WARNING: This is destructive and cannot be undone.
        """
        self.log.warning("clearing_database")
        await self.execute_write("MATCH (n) DETACH DELETE n")
        self.log.info("database_cleared")

    # Node operations

    async def create_module(self, module: ModuleInfo) -> str:
        """
        Create a module node in the graph.

        Args:
            module: ModuleInfo to create

        Returns:
            Node ID
        """
        query = """
        MERGE (m:Module {id: $id})
        SET m.path = $path,
            m.name = $name,
            m.package = $package,
            m.qualified_name = $qualified_name,
            m.hash = $hash,
            m.lines_of_code = $lines_of_code,
            m.docstring = $docstring,
            m.last_modified = datetime()
        RETURN m.id as id
        """
        params = {
            "id": str(module.id),
            "path": str(module.path),
            "name": module.name,
            "package": module.package,
            "qualified_name": module.qualified_name,
            "hash": module.hash,
            "lines_of_code": module.lines_of_code,
            "docstring": module.docstring,
        }
        result = await self.execute_query(query, params)
        return result[0]["id"] if result else str(module.id)

    async def create_class(self, cls: ClassInfo, parent_id: str) -> str:
        """
        Create a class node and link to parent.

        Args:
            cls: ClassInfo to create
            parent_id: ID of parent node (module or class)

        Returns:
            Node ID
        """
        query = """
        MATCH (parent {id: $parent_id})
        MERGE (c:Class {id: $id})
        SET c.name = $name,
            c.qualified_name = $qualified_name,
            c.hash = $hash,
            c.is_abstract = $is_abstract,
            c.bases = $bases,
            c.line_number = $line_number,
            c.docstring = $docstring
        MERGE (parent)-[:CONTAINS]->(c)
        RETURN c.id as id
        """
        params = {
            "parent_id": parent_id,
            "id": str(cls.id),
            "name": cls.name,
            "qualified_name": cls.qualified_name,
            "hash": "",  # Will be set by Merkle tree
            "is_abstract": cls.is_abstract,
            "bases": json.dumps(cls.bases),
            "line_number": cls.location.line if cls.location else None,
            "docstring": cls.docstring,
        }
        result = await self.execute_query(query, params)
        return result[0]["id"] if result else str(cls.id)

    async def create_function(self, func: FunctionInfo, parent_id: str) -> str:
        """
        Create a function node and link to parent.

        Args:
            func: FunctionInfo to create
            parent_id: ID of parent node (module or class)

        Returns:
            Node ID
        """
        query = """
        MATCH (parent {id: $parent_id})
        MERGE (f:Function {id: $id})
        SET f.name = $name,
            f.qualified_name = $qualified_name,
            f.hash = $hash,
            f.is_async = $is_async,
            f.is_generator = $is_generator,
            f.is_method = $is_method,
            f.is_classmethod = $is_classmethod,
            f.is_staticmethod = $is_staticmethod,
            f.is_property = $is_property,
            f.parameters = $parameters,
            f.return_type = $return_type,
            f.complexity = $complexity,
            f.line_number = $line_number,
            f.docstring = $docstring
        MERGE (parent)-[:CONTAINS]->(f)
        RETURN f.id as id
        """
        params = {
            "parent_id": parent_id,
            "id": str(func.id),
            "name": func.name,
            "qualified_name": func.qualified_name,
            "hash": func.body_hash,
            "is_async": func.is_async,
            "is_generator": func.is_generator,
            "is_method": func.is_method,
            "is_classmethod": func.is_classmethod,
            "is_staticmethod": func.is_staticmethod,
            "is_property": func.is_property,
            "parameters": json.dumps([p.as_dict for p in func.parameters]),
            "return_type": func.return_type,
            "complexity": func.complexity,
            "line_number": func.location.line if func.location else None,
            "docstring": func.docstring,
        }
        result = await self.execute_query(query, params)
        return result[0]["id"] if result else str(func.id)

    async def create_variable(self, var: VariableInfo, parent_id: str) -> str:
        """
        Create a variable node and link to parent.

        Args:
            var: VariableInfo to create
            parent_id: ID of parent node

        Returns:
            Node ID
        """
        query = """
        MATCH (parent {id: $parent_id})
        MERGE (v:Variable {id: $id})
        SET v.name = $name,
            v.scope = $scope,
            v.type_hint = $type_hint,
            v.initial_value = $initial_value,
            v.is_constant = $is_constant,
            v.line_number = $line_number
        MERGE (parent)-[:CONTAINS]->(v)
        RETURN v.id as id
        """
        params = {
            "parent_id": parent_id,
            "id": str(var.id),
            "name": var.name,
            "scope": var.scope,
            "type_hint": var.type_hint,
            "initial_value": var.initial_value,
            "is_constant": var.is_constant,
            "line_number": var.location.line if var.location else None,
        }
        result = await self.execute_query(query, params)
        return result[0]["id"] if result else str(var.id)

    async def create_relationship(self, rel: Relationship) -> None:
        """
        Create a relationship between two nodes.

        Args:
            rel: Relationship to create
        """
        rel_type = rel.relationship_type.value.upper()
        props = ", ".join(f"r.{k} = ${k}" for k in rel.properties.keys())

        query = f"""
        MATCH (source {{id: $source_id}})
        MATCH (target {{id: $target_id}})
        MERGE (source)-[r:{rel_type}]->(target)
        {f'SET {props}' if props else ''}
        """
        params = {
            "source_id": str(rel.source_id),
            "target_id": str(rel.target_id),
            **rel.properties,
        }
        await self.execute_write(query, params)

    # Bulk operations

    async def bulk_create_nodes(self, modules: list[ModuleInfo]) -> int:
        """
        Bulk create nodes from parsed modules.

        Args:
            modules: List of ModuleInfo to create

        Returns:
            Number of nodes created
        """
        total_created = 0

        for module in modules:
            await self.create_module(module)
            total_created += 1

            for cls in module.classes:
                await self._create_class_recursive(cls, str(module.id))
                total_created += 1 + len(cls.methods) + len(cls.all_variables)

            for func in module.functions:
                await self.create_function(func, str(module.id))
                total_created += 1

            for var in module.variables:
                await self.create_variable(var, str(module.id))
                total_created += 1

        self.log.info("bulk_nodes_created", count=total_created)
        return total_created

    async def _create_class_recursive(self, cls: ClassInfo, parent_id: str) -> None:
        """Recursively create a class and its members."""
        class_id = await self.create_class(cls, parent_id)

        for method in cls.methods:
            await self.create_function(method, class_id)

        for var in cls.all_variables:
            await self.create_variable(var, class_id)

        for nested in cls.nested_classes:
            await self._create_class_recursive(nested, class_id)

    async def bulk_create_relationships(self, relationships: list[Relationship]) -> int:
        """
        Bulk create relationships.

        Args:
            relationships: List of Relationship to create

        Returns:
            Number of relationships created
        """
        for rel in relationships:
            try:
                await self.create_relationship(rel)
            except Exception as e:
                self.log.warning(
                    "relationship_creation_failed",
                    source=str(rel.source_id),
                    target=str(rel.target_id),
                    error=str(e),
                )

        self.log.info("bulk_relationships_created", count=len(relationships))
        return len(relationships)

    # Query operations

    async def get_root_nodes(self) -> list[dict[str, Any]]:
        """
        Get all root-level modules with child counts.

        Returns:
            List of module nodes with metadata
        """
        query = """
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
        """
        return await self.execute_query(query)

    async def get_node_children(self, node_id: str) -> list[dict[str, Any]]:
        """
        Get immediate children of a node.

        Args:
            node_id: ID of the parent node

        Returns:
            List of child nodes with metadata
        """
        query = """
        MATCH (parent {id: $node_id})-[:CONTAINS]->(child)
        OPTIONAL MATCH (child)-[:CONTAINS]->(grandchild)
        WITH child, labels(child) as labels, count(grandchild) as child_count
        RETURN child.id as id,
               child.name as name,
               child.qualified_name as qualified_name,
               child.line_number as line_number,
               child.docstring as docstring,
               child_count,
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
               child.complexity as complexity
        ORDER BY
            CASE
                WHEN 'Class' IN labels THEN 0
                WHEN 'Function' IN labels THEN 1
                WHEN 'Variable' IN labels THEN 2
                ELSE 3
            END,
            child.line_number
        """
        return await self.execute_query(query, {"node_id": node_id})

    async def get_node_ancestors(self, node_id: str) -> list[dict[str, Any]]:
        """
        Get path from root to this node (for breadcrumbs).

        Args:
            node_id: ID of the node

        Returns:
            List of ancestor nodes from root to parent
        """
        query = """
        MATCH path = (root)-[:CONTAINS*0..]->(node {id: $node_id})
        WHERE NOT ()-[:CONTAINS]->(root)
        UNWIND nodes(path) as ancestor
        WITH ancestor, labels(ancestor) as labels
        RETURN ancestor.id as id,
               ancestor.name as name,
               ancestor.qualified_name as qualified_name,
               CASE
                   WHEN 'Module' IN labels THEN 'module'
                   WHEN 'Class' IN labels THEN 'class'
                   WHEN 'Function' IN labels THEN 'function'
                   WHEN 'Variable' IN labels THEN 'variable'
                   ELSE 'unknown'
               END as type
        """
        return await self.execute_query(query, {"node_id": node_id})

    async def search_nodes(self, query_text: str, limit: int = 50) -> list[dict[str, Any]]:
        """
        Full-text search across all node names.

        Args:
            query_text: Search query
            limit: Maximum results to return

        Returns:
            List of matching nodes with scores
        """
        # Escape special characters for Lucene query
        escaped = query_text.replace("~", "\\~").replace("*", "\\*")

        query = """
        CALL db.index.fulltext.queryNodes('node_name_search', $search_text)
        YIELD node, score
        WITH node, score, labels(node) as labels
        RETURN node.id as id,
               node.name as name,
               node.qualified_name as qualified_name,
               node.line_number as line_number,
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
        """
        return await self.execute_query(query, {"search_text": f"{escaped}~", "limit": limit})

    async def get_node_references(self, node_id: str) -> list[dict[str, Any]]:
        """
        Get all nodes that reference or are referenced by this node.

        Args:
            node_id: ID of the node

        Returns:
            List of related nodes with relationship types
        """
        query = """
        MATCH (node {id: $node_id})-[r]-(related)
        WHERE NOT type(r) = 'CONTAINS'
        WITH related, type(r) as rel_type, labels(related) as labels,
             CASE WHEN startNode(r) = node THEN 'outgoing' ELSE 'incoming' END as direction
        RETURN related.id as id,
               related.name as name,
               related.qualified_name as qualified_name,
               rel_type,
               direction,
               CASE
                   WHEN 'Module' IN labels THEN 'module'
                   WHEN 'Class' IN labels THEN 'class'
                   WHEN 'Function' IN labels THEN 'function'
                   WHEN 'Variable' IN labels THEN 'variable'
                   ELSE 'unknown'
               END as type
        """
        return await self.execute_query(query, {"node_id": node_id})

    async def get_node_by_id(self, node_id: str) -> dict[str, Any] | None:
        """
        Get a node by its ID.

        Args:
            node_id: ID of the node

        Returns:
            Node data or None if not found
        """
        query = """
        MATCH (n {id: $node_id})
        WITH n, labels(n) as labels
        OPTIONAL MATCH (n)-[:CONTAINS]->(child)
        WITH n, labels, count(child) as child_count
        RETURN n as node,
               labels,
               child_count
        """
        result = await self.execute_query(query, {"node_id": node_id})
        if not result:
            return None

        record = result[0]
        node_data = dict(record["node"])
        node_data["labels"] = record["labels"]
        node_data["child_count"] = record["child_count"]
        return node_data

    async def delete_module(self, module_path: str) -> int:
        """
        Delete a module and all its descendants.

        Args:
            module_path: Path of the module to delete

        Returns:
            Number of nodes deleted
        """
        query = """
        MATCH (m:Module {path: $path})
        OPTIONAL MATCH (m)-[:CONTAINS*]->(descendant)
        WITH m, collect(descendant) as descendants
        UNWIND [m] + descendants as node
        DETACH DELETE node
        RETURN count(*) as deleted_count
        """
        result = await self.execute_query(query, {"path": module_path})
        return result[0]["deleted_count"] if result else 0

    async def update_node_hash(self, node_id: str, new_hash: str) -> None:
        """
        Update the hash of a node (for Merkle tree updates).

        Args:
            node_id: ID of the node
            new_hash: New hash value
        """
        query = """
        MATCH (n {id: $node_id})
        SET n.hash = $hash
        """
        await self.execute_write(query, {"node_id": node_id, "hash": new_hash})

    async def expand_node(self, node_id: str) -> dict[str, Any]:
        """
        Get a node with all its outgoing connections for incremental loading.
        
        Returns the node, its direct children (via CONTAINS), 
        and outgoing edges (CALLS, IMPORTS, INHERITS).
        
        Args:
            node_id: Hierarchical ID of the node to expand
        
        Returns:
            Dictionary containing:
            - node: The expanded node
            - children: Direct child nodes (via CONTAINS)
            - outgoing: Nodes connected via CALLS/IMPORTS/INHERITS
            - edges: Edge details
        """
        query = """
        MATCH (n {id: $node_id})
        WITH n, labels(n) as node_labels
        
        // Get children via CONTAINS
        OPTIONAL MATCH (n)-[:CONTAINS]->(child)
        WITH n, node_labels, collect({
            id: child.id,
            name: child.name,
            type: head(labels(child)),
            qualified_name: child.qualified_name,
            line_number: child.line_number,
            docstring: child.docstring,
            is_async: child.is_async,
            complexity: child.complexity
        }) as children
        
        // Get outgoing relationships (CALLS, IMPORTS, INHERITS)
        OPTIONAL MATCH (n)-[r]->(target)
        WHERE type(r) IN ['CALLS', 'IMPORTS', 'INHERITS', 'INSTANTIATES']
        WITH n, node_labels, children, collect({
            target_id: target.id,
            target_name: target.name,
            target_type: head(labels(target)),
            edge_type: type(r),
            properties: properties(r)
        }) as outgoing
        
        RETURN n as node,
               node_labels as labels,
               [c IN children WHERE c.id IS NOT NULL] as children,
               [o IN outgoing WHERE o.target_id IS NOT NULL] as outgoing
        """
        result = await self.execute_query(query, {"node_id": node_id})
        
        if not result:
            return {"node": None, "children": [], "outgoing": [], "edges": []}
        
        record = result[0]
        node_data = dict(record["node"]) if record["node"] else {}
        node_data["labels"] = record["labels"]
        
        return {
            "node": node_data,
            "children": record["children"],
            "outgoing": record["outgoing"],
        }
    
    async def get_node_connections(self, node_id: str) -> list[dict[str, Any]]:
        """
        Get all nodes that this node connects to (outgoing) and are connected from (incoming).
        
        Excludes CONTAINS relationships.
        
        Args:
            node_id: ID of the node
        
        Returns:
            List of connected nodes with edge information
        """
        query = """
        MATCH (n {id: $node_id})
        OPTIONAL MATCH (n)-[out]->(target)
        WHERE NOT type(out) IN ['CONTAINS']
        WITH n, collect({
            id: target.id,
            name: target.name,
            type: head(labels(target)),
            qualified_name: target.qualified_name,
            edge_type: type(out),
            direction: 'outgoing',
            line_number: target.line_number
        }) as outgoing
        
        OPTIONAL MATCH (source)-[inc]->(n)
        WHERE NOT type(inc) IN ['CONTAINS']
        WITH outgoing, collect({
            id: source.id,
            name: source.name,
            type: head(labels(source)),
            qualified_name: source.qualified_name,
            edge_type: type(inc),
            direction: 'incoming',
            line_number: source.line_number
        }) as incoming
        
        RETURN [c IN outgoing + incoming WHERE c.id IS NOT NULL] as connections
        """
        result = await self.execute_query(query, {"node_id": node_id})
        return result[0]["connections"] if result else []

