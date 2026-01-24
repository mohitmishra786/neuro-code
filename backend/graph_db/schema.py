"""
NeuroCode Graph Schema.

Defines the Neo4j graph schema for code visualization.
Requires Python 3.11+.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeLabel(str, Enum):
    """Node labels in the graph."""

    PACKAGE = "Package"
    MODULE = "Module"
    CLASS = "Class"
    FUNCTION = "Function"
    VARIABLE = "Variable"
    IMPORT = "Import"


class RelationshipLabel(str, Enum):
    """Relationship labels in the graph."""

    CONTAINS = "CONTAINS"
    IMPORTS = "IMPORTS"
    CALLS = "CALLS"
    INSTANTIATES = "INSTANTIATES"
    INHERITS = "INHERITS"
    DECORATES = "DECORATES"
    DEFINES = "DEFINES"
    USES = "USES"
    RETURNS = "RETURNS"
    RAISES = "RAISES"


@dataclass(frozen=True)
class PropertyDefinition:
    """Definition of a node or relationship property."""

    name: str
    property_type: str  # "string", "int", "boolean", "float", "json", "datetime"
    required: bool = False
    indexed: bool = False
    unique: bool = False
    default: Any = None


@dataclass(frozen=True)
class NodeDefinition:
    """Definition of a node type."""

    label: NodeLabel
    properties: tuple[PropertyDefinition, ...]
    description: str = ""


@dataclass(frozen=True)
class RelationshipDefinition:
    """Definition of a relationship type."""

    label: RelationshipLabel
    source_labels: tuple[NodeLabel, ...]
    target_labels: tuple[NodeLabel, ...]
    properties: tuple[PropertyDefinition, ...]
    description: str = ""


class GraphSchema:
    """
    Defines the complete graph schema for NeuroCode.

    Provides schema validation, index creation, and migration support.
    """

    # Node type definitions
    NODES: dict[NodeLabel, NodeDefinition] = {
        NodeLabel.PACKAGE: NodeDefinition(
            label=NodeLabel.PACKAGE,
            description="Python package (directory with __init__.py)",
            properties=(
                PropertyDefinition("id", "string", required=True, unique=True, indexed=True),
                PropertyDefinition("path", "string", required=True, indexed=True),
                PropertyDefinition("name", "string", required=True, indexed=True),
                PropertyDefinition("qualified_name", "string", required=True, indexed=True),
                PropertyDefinition("parent_id", "string", indexed=True),
                PropertyDefinition("docstring", "string"),
            ),
        ),
        NodeLabel.MODULE: NodeDefinition(
            label=NodeLabel.MODULE,
            description="Python module (file)",
            properties=(
                PropertyDefinition("id", "string", required=True, unique=True, indexed=True),
                PropertyDefinition("path", "string", required=True, indexed=True),
                PropertyDefinition("name", "string", required=True, indexed=True),
                PropertyDefinition("package", "string", indexed=True),
                PropertyDefinition("qualified_name", "string", required=True, indexed=True),
                PropertyDefinition("hash", "string", indexed=True),
                PropertyDefinition("lines_of_code", "int"),
                PropertyDefinition("docstring", "string"),
                PropertyDefinition("last_modified", "datetime"),
            ),
        ),
        NodeLabel.CLASS: NodeDefinition(
            label=NodeLabel.CLASS,
            description="Python class",
            properties=(
                PropertyDefinition("id", "string", required=True, unique=True, indexed=True),
                PropertyDefinition("name", "string", required=True, indexed=True),
                PropertyDefinition("qualified_name", "string", required=True, indexed=True),
                PropertyDefinition("hash", "string", indexed=True),
                PropertyDefinition("is_abstract", "boolean", default=False),
                PropertyDefinition("bases", "json"),  # List of base class names
                PropertyDefinition("line_number", "int"),
                PropertyDefinition("docstring", "string"),
            ),
        ),
        NodeLabel.FUNCTION: NodeDefinition(
            label=NodeLabel.FUNCTION,
            description="Python function or method",
            properties=(
                PropertyDefinition("id", "string", required=True, unique=True, indexed=True),
                PropertyDefinition("name", "string", required=True, indexed=True),
                PropertyDefinition("qualified_name", "string", required=True, indexed=True),
                PropertyDefinition("hash", "string", indexed=True),
                PropertyDefinition("is_async", "boolean", default=False),
                PropertyDefinition("is_generator", "boolean", default=False),
                PropertyDefinition("is_method", "boolean", default=False),
                PropertyDefinition("is_classmethod", "boolean", default=False),
                PropertyDefinition("is_staticmethod", "boolean", default=False),
                PropertyDefinition("is_property", "boolean", default=False),
                PropertyDefinition("parameters", "json"),  # List of parameter info
                PropertyDefinition("return_type", "string"),
                PropertyDefinition("complexity", "int", default=1),
                PropertyDefinition("line_number", "int"),
                PropertyDefinition("docstring", "string"),
            ),
        ),
        NodeLabel.VARIABLE: NodeDefinition(
            label=NodeLabel.VARIABLE,
            description="Python variable",
            properties=(
                PropertyDefinition("id", "string", required=True, unique=True, indexed=True),
                PropertyDefinition("name", "string", required=True, indexed=True),
                PropertyDefinition("qualified_name", "string", indexed=True),
                PropertyDefinition("scope", "string"),  # module, class, function, instance
                PropertyDefinition("type_hint", "string"),
                PropertyDefinition("initial_value", "string"),
                PropertyDefinition("is_constant", "boolean", default=False),
                PropertyDefinition("line_number", "int"),
            ),
        ),
    }

    # Relationship type definitions
    RELATIONSHIPS: dict[RelationshipLabel, RelationshipDefinition] = {
        RelationshipLabel.CONTAINS: RelationshipDefinition(
            label=RelationshipLabel.CONTAINS,
            description="Parent contains child",
            source_labels=(NodeLabel.PACKAGE, NodeLabel.MODULE, NodeLabel.CLASS, NodeLabel.FUNCTION),
            target_labels=(NodeLabel.PACKAGE, NodeLabel.MODULE, NodeLabel.CLASS, NodeLabel.FUNCTION, NodeLabel.VARIABLE),
            properties=(
                PropertyDefinition("weight", "int", default=1),
                PropertyDefinition("order", "int"),
            ),
        ),
        RelationshipLabel.IMPORTS: RelationshipDefinition(
            label=RelationshipLabel.IMPORTS,
            description="Module imports another module",
            source_labels=(NodeLabel.MODULE,),
            target_labels=(NodeLabel.MODULE,),
            properties=(
                PropertyDefinition("import_type", "string"),  # absolute, relative
                PropertyDefinition("imported_names", "json"),
                PropertyDefinition("aliases", "json"),
            ),
        ),
        RelationshipLabel.CALLS: RelationshipDefinition(
            label=RelationshipLabel.CALLS,
            description="Function calls another function",
            source_labels=(NodeLabel.FUNCTION,),
            target_labels=(NodeLabel.FUNCTION,),
            properties=(
                PropertyDefinition("call_count", "int", default=1),
                PropertyDefinition("cross_module", "boolean", default=False),
            ),
        ),
        RelationshipLabel.INSTANTIATES: RelationshipDefinition(
            label=RelationshipLabel.INSTANTIATES,
            description="Function instantiates a class",
            source_labels=(NodeLabel.FUNCTION,),
            target_labels=(NodeLabel.CLASS,),
            properties=(
                PropertyDefinition("count", "int", default=1),
            ),
        ),
        RelationshipLabel.INHERITS: RelationshipDefinition(
            label=RelationshipLabel.INHERITS,
            description="Class inherits from another class",
            source_labels=(NodeLabel.CLASS,),
            target_labels=(NodeLabel.CLASS,),
            properties=(
                PropertyDefinition("order", "int"),  # MRO order
            ),
        ),
        RelationshipLabel.DECORATES: RelationshipDefinition(
            label=RelationshipLabel.DECORATES,
            description="Decorator decorates function or class",
            source_labels=(NodeLabel.FUNCTION,),
            target_labels=(NodeLabel.FUNCTION, NodeLabel.CLASS),
            properties=(
                PropertyDefinition("decorator_order", "int"),
            ),
        ),
        RelationshipLabel.DEFINES: RelationshipDefinition(
            label=RelationshipLabel.DEFINES,
            description="Function defines a local variable",
            source_labels=(NodeLabel.FUNCTION,),
            target_labels=(NodeLabel.VARIABLE,),
            properties=(
                PropertyDefinition("scope", "string"),
            ),
        ),
        RelationshipLabel.USES: RelationshipDefinition(
            label=RelationshipLabel.USES,
            description="Function uses a variable",
            source_labels=(NodeLabel.FUNCTION,),
            target_labels=(NodeLabel.VARIABLE,),
            properties=(
                PropertyDefinition("access_type", "string"),  # read, write, both
                PropertyDefinition("count", "int", default=1),
            ),
        ),
    }

    @classmethod
    def get_index_creation_statements(cls) -> list[str]:
        """
        Generate Cypher statements to create all indexes.

        Returns:
            List of Cypher CREATE INDEX statements
        """
        statements: list[str] = []

        for node_def in cls.NODES.values():
            for prop in node_def.properties:
                if prop.unique:
                    statements.append(
                        f"CREATE CONSTRAINT {node_def.label.value.lower()}_{prop.name}_unique "
                        f"IF NOT EXISTS FOR (n:{node_def.label.value}) REQUIRE n.{prop.name} IS UNIQUE"
                    )
                elif prop.indexed:
                    statements.append(
                        f"CREATE INDEX {node_def.label.value.lower()}_{prop.name}_idx "
                        f"IF NOT EXISTS FOR (n:{node_def.label.value}) ON (n.{prop.name})"
                    )

        # Full-text search index for names
        statements.append(
            "CREATE FULLTEXT INDEX node_name_search IF NOT EXISTS "
            "FOR (n:Package|Module|Class|Function|Variable) ON EACH [n.name, n.qualified_name]"
        )

        return statements

    @classmethod
    def get_constraint_creation_statements(cls) -> list[str]:
        """
        Generate Cypher statements to create all constraints.

        Returns:
            List of Cypher CREATE CONSTRAINT statements
        """
        statements: list[str] = []

        for node_def in cls.NODES.values():
            # Require ID for all node types
            statements.append(
                f"CREATE CONSTRAINT {node_def.label.value.lower()}_id_exists "
                f"IF NOT EXISTS FOR (n:{node_def.label.value}) REQUIRE n.id IS NOT NULL"
            )

        return statements

    @classmethod
    def validate_node(cls, label: NodeLabel, properties: dict[str, Any]) -> list[str]:
        """
        Validate node properties against schema.

        Args:
            label: Node label
            properties: Node properties to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors: list[str] = []
        node_def = cls.NODES.get(label)

        if not node_def:
            errors.append(f"Unknown node label: {label}")
            return errors

        for prop_def in node_def.properties:
            if prop_def.required and prop_def.name not in properties:
                errors.append(f"Missing required property: {prop_def.name}")

        return errors

    @classmethod
    def get_node_properties(cls, label: NodeLabel) -> list[str]:
        """Get list of property names for a node type."""
        node_def = cls.NODES.get(label)
        if not node_def:
            return []
        return [p.name for p in node_def.properties]
