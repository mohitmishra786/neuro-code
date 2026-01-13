"""
NeuroCode Relationship Extractor.

Builds bidirectional relationships between code elements.
Requires Python 3.11+.
"""

from collections import defaultdict
from pathlib import Path
from typing import Iterator
from uuid import UUID

from parser.models import (
    ClassInfo,
    FunctionInfo,
    ModuleInfo,
    Relationship,
    RelationshipType,
    AccessType,
)
from utils.logger import LoggerMixin


class RelationshipExtractor(LoggerMixin):
    """
    Extracts relationships between code elements.

    Builds bidirectional relationships such as:
    - CONTAINS: Module -> Class -> Method -> Variable
    - IMPORTS: Module -> Module
    - CALLS: Function -> Function
    - INHERITS: Class -> Class
    - USES: Function -> Variable
    """

    def __init__(self) -> None:
        """Initialize the relationship extractor."""
        # Maps qualified names to UUIDs for cross-referencing
        self._name_to_id: dict[str, UUID] = {}
        # Maps module paths to qualified names
        self._path_to_module: dict[Path, str] = {}
        # Call graph: caller -> list of callees
        self._call_graph: dict[str, list[str]] = defaultdict(list)

    def extract_relationships(self, modules: list[ModuleInfo]) -> list[Relationship]:
        """
        Extract all relationships from a list of parsed modules.

        Args:
            modules: List of parsed ModuleInfo objects

        Returns:
            List of Relationship objects
        """
        # First pass: build name-to-ID mapping
        self._build_name_mapping(modules)

        # Second pass: extract relationships
        relationships: list[Relationship] = []

        for module in modules:
            # Module contains classes
            for cls in module.classes:
                relationships.append(
                    Relationship(
                        source_id=module.id,
                        target_id=cls.id,
                        relationship_type=RelationshipType.CONTAINS,
                        properties={"weight": 1},
                    )
                )
                # Extract class relationships
                relationships.extend(self._extract_class_relationships(cls, module))

            # Module contains functions
            for func in module.functions:
                relationships.append(
                    Relationship(
                        source_id=module.id,
                        target_id=func.id,
                        relationship_type=RelationshipType.CONTAINS,
                        properties={"weight": 1},
                    )
                )
                # Extract function relationships
                relationships.extend(self._extract_function_relationships(func, module))

            # Module contains variables
            for var in module.variables:
                relationships.append(
                    Relationship(
                        source_id=module.id,
                        target_id=var.id,
                        relationship_type=RelationshipType.CONTAINS,
                        properties={"weight": 1},
                    )
                )

            # Module imports
            relationships.extend(self._extract_import_relationships(module))

        # Extract cross-module call relationships
        relationships.extend(self._extract_cross_module_calls())

        self.log.info(
            "extracted_relationships",
            module_count=len(modules),
            relationship_count=len(relationships),
        )

        return relationships

    def _build_name_mapping(self, modules: list[ModuleInfo]) -> None:
        """Build a mapping from qualified names to UUIDs."""
        self._name_to_id.clear()
        self._path_to_module.clear()

        for module in modules:
            self._name_to_id[module.qualified_name] = module.id
            self._path_to_module[module.path] = module.qualified_name

            for cls in module.classes:
                self._register_class(cls)

            for func in module.functions:
                self._name_to_id[func.qualified_name] = func.id

            for var in module.variables:
                qualified_var = f"{module.qualified_name}.{var.name}"
                self._name_to_id[qualified_var] = var.id

    def _register_class(self, cls: ClassInfo) -> None:
        """Register a class and all its members."""
        self._name_to_id[cls.qualified_name] = cls.id

        for method in cls.methods:
            self._name_to_id[method.qualified_name] = method.id

        for var in cls.all_variables:
            qualified_var = f"{cls.qualified_name}.{var.name}"
            self._name_to_id[qualified_var] = var.id

        for nested in cls.nested_classes:
            self._register_class(nested)

    def _extract_class_relationships(
        self, cls: ClassInfo, module: ModuleInfo
    ) -> Iterator[Relationship]:
        """Extract relationships for a class."""
        # Class contains methods
        for method in cls.methods:
            yield Relationship(
                source_id=cls.id,
                target_id=method.id,
                relationship_type=RelationshipType.CONTAINS,
                properties={"weight": 1},
            )
            # Extract method relationships
            yield from self._extract_function_relationships(method, module, cls)

        # Class contains variables
        for var in cls.all_variables:
            yield Relationship(
                source_id=cls.id,
                target_id=var.id,
                relationship_type=RelationshipType.CONTAINS,
                properties={"weight": 1, "scope": var.scope},
            )

        # Class inheritance
        for i, base in enumerate(cls.bases):
            base_id = self._resolve_name(base, module)
            if base_id:
                yield Relationship(
                    source_id=cls.id,
                    target_id=base_id,
                    relationship_type=RelationshipType.INHERITS,
                    properties={"order": i},
                )

        # Decorator relationships
        for i, decorator in enumerate(cls.decorators):
            decorator_id = self._resolve_name(decorator.name, module)
            if decorator_id:
                yield Relationship(
                    source_id=decorator_id,
                    target_id=cls.id,
                    relationship_type=RelationshipType.DECORATES,
                    properties={"decorator_order": i},
                )

        # Nested classes
        for nested in cls.nested_classes:
            yield Relationship(
                source_id=cls.id,
                target_id=nested.id,
                relationship_type=RelationshipType.CONTAINS,
                properties={"weight": 1},
            )
            yield from self._extract_class_relationships(nested, module)

    def _extract_function_relationships(
        self,
        func: FunctionInfo,
        module: ModuleInfo,
        parent_class: ClassInfo | None = None,
    ) -> Iterator[Relationship]:
        """Extract relationships for a function."""
        # Function contains local variables
        for var in func.variables:
            yield Relationship(
                source_id=func.id,
                target_id=var.id,
                relationship_type=RelationshipType.DEFINES,
                properties={"scope": "local"},
            )

        # Function calls
        call_counts: dict[str, int] = defaultdict(int)
        for call in func.calls:
            call_counts[call] += 1

        for call_name, count in call_counts.items():
            callee_id = self._resolve_name(call_name, module, parent_class)
            if callee_id:
                yield Relationship(
                    source_id=func.id,
                    target_id=callee_id,
                    relationship_type=RelationshipType.CALLS,
                    properties={"call_count": count},
                )
            else:
                # Store for cross-module resolution later
                self._call_graph[func.qualified_name].append(call_name)

        # Decorator relationships
        for i, decorator in enumerate(func.decorators):
            decorator_id = self._resolve_name(decorator.name, module)
            if decorator_id:
                yield Relationship(
                    source_id=decorator_id,
                    target_id=func.id,
                    relationship_type=RelationshipType.DECORATES,
                    properties={"decorator_order": i},
                )

        # Class instantiation (calls to class constructors)
        for call_name, count in call_counts.items():
            target_id = self._resolve_name(call_name, module, parent_class)
            if target_id and call_name[0].isupper():  # Heuristic: class names are capitalized
                yield Relationship(
                    source_id=func.id,
                    target_id=target_id,
                    relationship_type=RelationshipType.INSTANTIATES,
                    properties={"count": count},
                )

    def _extract_import_relationships(self, module: ModuleInfo) -> Iterator[Relationship]:
        """Extract import relationships."""
        for imp in module.imports:
            # Resolve the imported module
            if imp.is_relative:
                # Handle relative imports
                imported_module = self._resolve_relative_import(
                    module.package,
                    imp.module_name,
                    imp.relative_level,
                )
            else:
                imported_module = imp.module_name

            target_id = self._name_to_id.get(imported_module)
            if target_id:
                yield Relationship(
                    source_id=module.id,
                    target_id=target_id,
                    relationship_type=RelationshipType.IMPORTS,
                    properties={
                        "import_type": "relative" if imp.is_relative else "absolute",
                        "imported_names": imp.imported_names,
                    },
                )

    def _extract_cross_module_calls(self) -> Iterator[Relationship]:
        """Extract call relationships that span modules."""
        for caller_name, callees in self._call_graph.items():
            caller_id = self._name_to_id.get(caller_name)
            if not caller_id:
                continue

            for callee_name in callees:
                # Try to find the callee in other modules
                callee_id = self._name_to_id.get(callee_name)
                if callee_id:
                    yield Relationship(
                        source_id=caller_id,
                        target_id=callee_id,
                        relationship_type=RelationshipType.CALLS,
                        properties={"call_count": 1, "cross_module": True},
                    )

    def _resolve_name(
        self,
        name: str,
        module: ModuleInfo,
        parent_class: ClassInfo | None = None,
    ) -> UUID | None:
        """
        Resolve a name to its UUID.

        Searches in this order:
        1. Current class (if applicable)
        2. Current module
        3. Imported names
        4. Builtins (not tracked)

        Args:
            name: Name to resolve
            module: Current module context
            parent_class: Parent class context (if in a method)

        Returns:
            UUID if found, None otherwise
        """
        # Handle attribute access (a.b.c)
        if "." in name:
            parts = name.split(".")
            # Try to resolve the full qualified name
            full_name = name
            if full_name in self._name_to_id:
                return self._name_to_id[full_name]

            # Try module-qualified
            full_name = f"{module.qualified_name}.{name}"
            if full_name in self._name_to_id:
                return self._name_to_id[full_name]

            # Try class-qualified
            if parent_class:
                full_name = f"{parent_class.qualified_name}.{name}"
                if full_name in self._name_to_id:
                    return self._name_to_id[full_name]

            # Try first part only
            name = parts[0]

        # Check if it's a method in the current class
        if parent_class:
            qualified = f"{parent_class.qualified_name}.{name}"
            if qualified in self._name_to_id:
                return self._name_to_id[qualified]

        # Check if it's in the current module
        qualified = f"{module.qualified_name}.{name}"
        if qualified in self._name_to_id:
            return self._name_to_id[qualified]

        # Check imports
        for imp in module.imports:
            if name in imp.imported_names:
                # Found in a from-import
                imported_qualified = f"{imp.module_name}.{name}"
                if imported_qualified in self._name_to_id:
                    return self._name_to_id[imported_qualified]
            elif name in imp.aliases.values():
                # Found as an alias
                for original, alias in imp.aliases.items():
                    if alias == name:
                        imported_qualified = f"{imp.module_name}.{original}"
                        if imported_qualified in self._name_to_id:
                            return self._name_to_id[imported_qualified]
            elif name == imp.module_name.split(".")[-1]:
                # Direct module import
                if imp.module_name in self._name_to_id:
                    return self._name_to_id[imp.module_name]

        # Check global name registry
        if name in self._name_to_id:
            return self._name_to_id[name]

        return None

    def _resolve_relative_import(
        self,
        current_package: str,
        module_name: str,
        relative_level: int,
    ) -> str:
        """
        Resolve a relative import to an absolute module path.

        Args:
            current_package: Current package path (e.g., "mypackage.subpackage")
            module_name: Module name from import (may be empty for "from . import x")
            relative_level: Number of dots (1 for ".", 2 for "..", etc.)

        Returns:
            Absolute module path
        """
        if not current_package:
            return module_name

        parts = current_package.split(".")

        # Go up n-1 levels (one dot means current package)
        if relative_level > len(parts):
            # Import goes beyond package root
            return module_name

        base_parts = parts[: len(parts) - relative_level + 1]
        base = ".".join(base_parts)

        if module_name:
            return f"{base}.{module_name}"
        return base

    def get_node_id(self, qualified_name: str) -> UUID | None:
        """Get the UUID for a qualified name."""
        return self._name_to_id.get(qualified_name)

    def get_all_relationships_for_node(
        self, node_id: UUID, relationships: list[Relationship]
    ) -> list[Relationship]:
        """Get all relationships involving a specific node."""
        return [
            r
            for r in relationships
            if r.source_id == node_id or r.target_id == node_id
        ]

    def build_dependency_graph(
        self, relationships: list[Relationship]
    ) -> dict[UUID, set[UUID]]:
        """Build a dependency graph from relationships."""
        graph: dict[UUID, set[UUID]] = defaultdict(set)

        for rel in relationships:
            if rel.relationship_type in (
                RelationshipType.CALLS,
                RelationshipType.IMPORTS,
                RelationshipType.USES,
                RelationshipType.INSTANTIATES,
            ):
                graph[rel.source_id].add(rel.target_id)

        return dict(graph)
