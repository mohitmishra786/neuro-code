"""
NeuroCode Parser Data Models.

Defines the data structures for parsed code elements.
Uses hierarchical string IDs for deterministic navigation.
Requires Python 3.11+.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class NodeType(str, Enum):
    """Types of nodes in the code graph."""

    PACKAGE = "package"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    IMPORT = "import"
    DECORATOR = "decorator"
    PARAMETER = "parameter"


class RelationshipType(str, Enum):
    """Types of relationships between nodes."""

    CONTAINS = "contains"
    IMPORTS = "imports"
    CALLS = "calls"
    INSTANTIATES = "instantiates"
    INHERITS = "inherits"
    DECORATES = "decorates"
    DEFINES = "defines"
    USES = "uses"
    RETURNS = "returns"
    RAISES = "raises"
    READS = "reads"
    WRITES = "writes"


class AccessType(str, Enum):
    """Variable access types."""

    READ = "read"
    WRITE = "write"
    BOTH = "both"


def generate_node_id(file_path: Path | str, *scope_parts: str) -> str:
    """
    Generate a hierarchical node ID.
    
    Format: file_path::scope1::scope2::...
    
    Examples:
        - src/vaak/core/math_engine.py
        - src/vaak/core/math_engine.py::ValidatorClass
        - src/vaak/core/math_engine.py::ValidatorClass::validate_output
    """
    base = str(file_path) if file_path else ""
    if scope_parts:
        return f"{base}::{'::'.join(scope_parts)}"
    return base


@dataclass(slots=True)
class SourceLocation:
    """Source code location information with byte offsets."""

    line: int
    column: int
    end_line: int
    end_column: int
    start_byte: int = 0
    end_byte: int = 0

    @property
    def as_dict(self) -> dict[str, int]:
        """Convert to dictionary for serialization."""
        return {
            "line": self.line,
            "column": self.column,
            "end_line": self.end_line,
            "end_column": self.end_column,
            "start_byte": self.start_byte,
            "end_byte": self.end_byte,
        }


@dataclass(slots=True)
class ParameterInfo:
    """Function/method parameter information."""

    name: str
    type_hint: str | None = None
    default_value: str | None = None
    is_args: bool = False
    is_kwargs: bool = False

    @property
    def as_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "type_hint": self.type_hint,
            "default_value": self.default_value,
            "is_args": self.is_args,
            "is_kwargs": self.is_kwargs,
        }


@dataclass(slots=True)
class DecoratorInfo:
    """Decorator information."""

    name: str
    arguments: list[str] = field(default_factory=list)
    location: SourceLocation | None = None

    @property
    def qualified_name(self) -> str:
        """Get decorator call signature."""
        if self.arguments:
            return f"@{self.name}({', '.join(self.arguments)})"
        return f"@{self.name}"


@dataclass(slots=True)
class ImportInfo:
    """Import statement information."""

    id: str = ""  # Hierarchical ID: file_path::import_module
    module_name: str = ""
    imported_names: list[str] = field(default_factory=list)
    aliases: dict[str, str] = field(default_factory=dict)
    is_relative: bool = False
    relative_level: int = 0
    location: SourceLocation | None = None
    # Resolved target module path (set during linking)
    resolved_module: str = ""

    @property
    def is_from_import(self) -> bool:
        """Check if this is a 'from x import y' style import."""
        return len(self.imported_names) > 0

    @property
    def absolute_module(self) -> str:
        """Get the absolute module path (without relative dots)."""
        return self.resolved_module or self.module_name


@dataclass(slots=True)
class VariableInfo:
    """Variable information."""

    id: str = ""  # Hierarchical ID: file_path::class?::function?::var_name
    name: str = ""
    type_hint: str | None = None
    initial_value: str | None = None
    scope: str = "module"  # module, class, function
    is_constant: bool = False
    location: SourceLocation | None = None

    @property
    def as_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "type_hint": self.type_hint,
            "initial_value": self.initial_value,
            "scope": self.scope,
            "is_constant": self.is_constant,
            "line_number": self.location.line if self.location else None,
        }


@dataclass(slots=True)
class SymbolReference:
    """A reference to a symbol (call, read, write)."""
    
    name: str  # The symbol name as written in code
    ref_type: str  # "call", "read", "write", "import"
    location: SourceLocation | None = None
    resolved_id: str = ""  # Resolved target ID (set during linking)
    context_id: str = ""  # ID of containing function/class


@dataclass(slots=True)
class FunctionInfo:
    """Function or method information."""

    id: str = ""  # Hierarchical ID: file_path::class?::function_name
    name: str = ""
    qualified_name: str = ""
    parameters: list[ParameterInfo] = field(default_factory=list)
    return_type: str | None = None
    decorators: list[DecoratorInfo] = field(default_factory=list)
    docstring: str | None = None
    is_async: bool = False
    is_generator: bool = False
    is_method: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False
    is_property: bool = False
    complexity: int = 1  # Cyclomatic complexity
    location: SourceLocation | None = None
    variables: list[VariableInfo] = field(default_factory=list)
    # Raw call names as they appear in source (pre-resolution)
    calls: list[str] = field(default_factory=list)
    # Detailed references with resolution info
    references: list[SymbolReference] = field(default_factory=list)
    body_hash: str = ""  # Hash of function body for change detection

    @property
    def signature(self) -> str:
        """Get function signature string."""
        params = ", ".join(
            f"{p.name}: {p.type_hint}" if p.type_hint else p.name for p in self.parameters
        )
        ret = f" -> {self.return_type}" if self.return_type else ""
        async_prefix = "async " if self.is_async else ""
        return f"{async_prefix}def {self.name}({params}){ret}"

    @property
    def as_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "qualified_name": self.qualified_name,
            "parameters": [p.as_dict for p in self.parameters],
            "return_type": self.return_type,
            "docstring": self.docstring,
            "is_async": self.is_async,
            "is_generator": self.is_generator,
            "is_method": self.is_method,
            "complexity": self.complexity,
            "line_number": self.location.line if self.location else None,
            "start_byte": self.location.start_byte if self.location else None,
            "end_byte": self.location.end_byte if self.location else None,
        }


@dataclass(slots=True)
class ClassInfo:
    """Class information."""

    id: str = ""  # Hierarchical ID: file_path::class_name
    name: str = ""
    qualified_name: str = ""
    bases: list[str] = field(default_factory=list)
    decorators: list[DecoratorInfo] = field(default_factory=list)
    docstring: str | None = None
    is_abstract: bool = False
    methods: list[FunctionInfo] = field(default_factory=list)
    class_variables: list[VariableInfo] = field(default_factory=list)
    instance_variables: list[VariableInfo] = field(default_factory=list)
    nested_classes: list["ClassInfo"] = field(default_factory=list)
    location: SourceLocation | None = None
    # Resolved base class IDs (set during linking)
    resolved_bases: list[str] = field(default_factory=list)

    @property
    def all_variables(self) -> list[VariableInfo]:
        """Get all variables (class and instance)."""
        return self.class_variables + self.instance_variables

    @property
    def as_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "qualified_name": self.qualified_name,
            "bases": self.bases,
            "docstring": self.docstring,
            "is_abstract": self.is_abstract,
            "method_count": len(self.methods),
            "line_number": self.location.line if self.location else None,
            "start_byte": self.location.start_byte if self.location else None,
            "end_byte": self.location.end_byte if self.location else None,
        }

@dataclass(slots=True)
class PackageInfo:
    """Package (directory) information for hierarchical structure."""

    id: str = ""  # Hierarchical ID: relative directory path
    path: Path = field(default_factory=Path)
    name: str = ""  # Directory name
    qualified_name: str = ""  # Python dotted name (e.g., vaak.integrity)
    parent_id: str = ""  # Parent package ID (empty for root)
    docstring: str | None = None  # From __init__.py if present
    child_packages: list[str] = field(default_factory=list)  # Child package IDs
    child_modules: list[str] = field(default_factory=list)  # Child module IDs

    @property
    def as_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "qualified_name": self.qualified_name,
            "parent_id": self.parent_id,
            "child_count": len(self.child_packages) + len(self.child_modules),
        }


@dataclass(slots=True)
class ModuleInfo:
    """Module (file) information."""

    id: str = ""  # Hierarchical ID: relative file path from project root
    path: Path = field(default_factory=Path)
    name: str = ""
    package: str = ""
    docstring: str | None = None
    imports: list[ImportInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    variables: list[VariableInfo] = field(default_factory=list)
    lines_of_code: int = 0
    hash: str = ""  # Merkle tree hash

    @property
    def qualified_name(self) -> str:
        """Get fully qualified module name."""
        if self.package:
            return f"{self.package}.{self.name}"
        return self.name

    @property
    def as_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "path": str(self.path),
            "name": self.name,
            "package": self.package,
            "qualified_name": self.qualified_name,
            "docstring": self.docstring,
            "lines_of_code": self.lines_of_code,
            "class_count": len(self.classes),
            "function_count": len(self.functions),
            "import_count": len(self.imports),
        }


@dataclass(slots=True)
class Relationship:
    """Relationship between two nodes."""

    source_id: str  # Hierarchical ID
    target_id: str  # Hierarchical ID
    relationship_type: RelationshipType
    properties: dict[str, Any] = field(default_factory=dict)

    @property
    def as_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.relationship_type.value,
            "properties": self.properties,
        }


@dataclass(slots=True)
class ParseResult:
    """Result of parsing a Python file or directory."""

    modules: list[ModuleInfo] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    parse_time_ms: float = 0.0

    @property
    def success(self) -> bool:
        """Check if parsing completed without critical errors."""
        return len(self.modules) > 0

    @property
    def total_classes(self) -> int:
        """Count total classes across all modules."""
        return sum(len(m.classes) for m in self.modules)

    @property
    def total_functions(self) -> int:
        """Count total functions across all modules."""
        return sum(len(m.functions) for m in self.modules)

    def merge(self, other: "ParseResult") -> "ParseResult":
        """Merge another parse result into this one."""
        return ParseResult(
            modules=self.modules + other.modules,
            relationships=self.relationships + other.relationships,
            errors=self.errors + other.errors,
            parse_time_ms=self.parse_time_ms + other.parse_time_ms,
        )
