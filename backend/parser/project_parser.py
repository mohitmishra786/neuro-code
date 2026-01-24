"""
NeuroCode Deep-Resolution Project Parser.

Three-pass architecture for complete cross-file symbol resolution:
- Pass 1 (Discovery): Map file paths to module IDs
- Pass 2 (Local AST): Extract definitions and references from each file
- Pass 3 (Linker): Resolve cross-file references and create edges

Requires Python 3.11+.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Node, Query

from parser.models import (
    ClassInfo,
    DecoratorInfo,
    FunctionInfo,
    ImportInfo,
    ModuleInfo,
    PackageInfo,
    ParameterInfo,
    Relationship,
    RelationshipType,
    SourceLocation,
    SymbolReference,
    VariableInfo,
)
from utils.logger import LoggerMixin


@dataclass
class SymbolEntry:
    """Entry in the project-wide symbol table."""
    id: str                      # Hierarchical ID
    name: str                    # Simple name
    kind: str                    # module, class, function, variable
    file_path: Path
    qualified_name: str          # Python dotted name (e.g., vaak.core.math_engine)
    parent_id: str | None = None
    location: SourceLocation | None = None


@dataclass
class ImportEntry:
    """Resolved import mapping."""
    alias: str                   # Name used in code
    qualified_name: str          # Full Python dotted name
    target_id: str               # Resolved hierarchical ID
    imported_names: list[str] = field(default_factory=list)


class ProjectParser(LoggerMixin):
    """
    Three-pass parser for deep symbol resolution.
    
    Parses an entire project directory, builds a symbol table,
    and resolves cross-file references to create direct edges.
    """
    
    PYTHON_LANG = Language(tspython.language())
    
    # Tree-sitter queries for extracting code structure
    DEFINITION_QUERY_STR = """
    ; Function definitions
    (function_definition
      name: (identifier) @func.name
      parameters: (parameters) @func.params
      return_type: (type)? @func.return_type
      body: (block) @func.body) @func.def
    
    ; Class definitions
    (class_definition
      name: (identifier) @class.name
      superclasses: (argument_list)? @class.bases
      body: (block) @class.body) @class.def
    
    ; Module-level assignments (variables/constants)
    (module
      (expression_statement
        (assignment
          left: (identifier) @var.name
          right: (_) @var.value))) @var.def
    
    ; Decorated definitions
    (decorated_definition
      (decorator)+ @dec.list
      definition: (_) @dec.target)
    """
    
    IMPORT_QUERY_STR = """
    ; import x, y, z
    (import_statement
      name: (dotted_name) @import.module) @import.stmt
    
    ; import x as y
    (import_statement
      name: (aliased_import
        name: (dotted_name) @import.module
        alias: (identifier) @import.alias)) @import.alias_stmt
    
    ; from x import y, z
    (import_from_statement
      module_name: (dotted_name)? @from.module
      module_name: (relative_import)? @from.relative
      name: (dotted_name) @from.name) @from.stmt
    
    ; from x import y as z
    (import_from_statement
      module_name: (dotted_name)? @from.module
      module_name: (relative_import)? @from.relative
      name: (aliased_import
        name: (dotted_name) @from.name
        alias: (identifier) @from.alias)) @from.alias_stmt
    """
    
    REFERENCE_QUERY_STR = """
    ; Function/method calls
    (call
      function: (identifier) @call.name) @call.simple
    
    ; Method calls: obj.method()
    (call
      function: (attribute
        object: (_) @call.object
        attribute: (identifier) @call.method)) @call.method
    
    ; Attribute access: obj.attr
    (attribute
      object: (identifier) @attr.object
      attribute: (identifier) @attr.name) @attr.access
    
    ; Name references
    (identifier) @ref.name
    """
    
    # Patterns to ignore during file discovery
    IGNORE_PATTERNS = [
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "node_modules",
        ".pytest_cache",
        ".mypy_cache",
        "build",
        "dist",
        ".egg-info",
        ".tox",
    ]
    
    def __init__(self, root_path: Path):
        """
        Initialize the project parser.
        
        Args:
            root_path: Root directory of the Python project
        """
        self.root = root_path.resolve()
        self.parser = Parser(self.PYTHON_LANG)
        
        # Compile queries
        self._def_query = Query(self.PYTHON_LANG, self.DEFINITION_QUERY_STR)
        self._import_query = Query(self.PYTHON_LANG, self.IMPORT_QUERY_STR)
        self._ref_query = Query(self.PYTHON_LANG, self.REFERENCE_QUERY_STR)
        
        # Project-wide symbol table: id -> SymbolEntry
        self.symbols: dict[str, SymbolEntry] = {}
        
        # Qualified name to ID mapping for resolution
        self.qualified_to_id: dict[str, str] = {}
        
        # Per-file import mappings: file_id -> {alias -> ImportEntry}
        self.file_imports: dict[str, dict[str, ImportEntry]] = defaultdict(dict)
        
        # Collected packages (directories with __init__.py)
        self.packages: list[PackageInfo] = []
        
        # Collected modules
        self.modules: list[ModuleInfo] = []
        
        # Collected relationships
        self.relationships: list[Relationship] = []
        
        # Parse errors
        self.errors: list[str] = []
        
        # Package ID mapping: relative path -> PackageInfo
        self._package_map: dict[str, PackageInfo] = {}
    
    def parse_project(self) -> tuple[list[PackageInfo], list[ModuleInfo], list[Relationship]]:
        """
        Execute 3-pass parsing on the entire project.
        
        Returns:
            Tuple of (packages, modules, relationships)
        """
        # Find all Python files
        files = self._discover_files()
        self.log.info("discovered_files", count=len(files), root=str(self.root))
        
        if not files:
            self.log.warning("no_python_files_found", root=str(self.root))
            return [], [], []
        
        # Pass 0: Discover packages (directories with __init__.py)
        self._pass0_packages(files)
        self.log.info("pass0_complete", packages=len(self.packages))
        
        # Pass 1: Discovery - build file -> module ID mapping
        self._pass1_discovery(files)
        self.log.info("pass1_complete", symbols=len(self.symbols))
        
        # Pass 2: Local AST - extract definitions and references
        self._pass2_local_ast(files)
        self.log.info("pass2_complete", modules=len(self.modules))
        
        # Pass 3: Linker - resolve cross-file references
        self._pass3_linker()
        self.log.info("pass3_complete", relationships=len(self.relationships))
        
        return self.packages, self.modules, self.relationships
    
    def _discover_files(self) -> list[Path]:
        """Find all Python files in the project."""
        files = []
        for file_path in self.root.rglob("*.py"):
            if self._should_ignore(file_path):
                continue
            files.append(file_path)
        return sorted(files)
    
    def _should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored."""
        path_str = str(path)
        for pattern in self.IGNORE_PATTERNS:
            if pattern in path_str:
                return True
        return False
    
    def _get_relative_path(self, file_path: Path) -> str:
        """Get path relative to project root."""
        try:
            return str(file_path.relative_to(self.root))
        except ValueError:
            return str(file_path)
    
    def _path_to_module_name(self, file_path: Path) -> tuple[str, str]:
        """
        Convert file path to Python module name and package.
        
        Returns:
            Tuple of (module_name, package_name)
        """
        rel_path = self._get_relative_path(file_path)
        
        # Remove .py extension
        if rel_path.endswith(".py"):
            rel_path = rel_path[:-3]
        
        # Convert path separators to dots
        parts = rel_path.replace("/", ".").replace("\\", ".").split(".")
        
        # Handle __init__.py - use parent package name
        if parts[-1] == "__init__":
            parts = parts[:-1]
            if not parts:
                parts = ["__init__"]
        
        module_name = parts[-1] if parts else ""
        package_name = ".".join(parts[:-1]) if len(parts) > 1 else ""
        
        return module_name, package_name
    
    # =========================================================================
    # Pass 0: Package Discovery
    # =========================================================================
    
    def _pass0_packages(self, files: list[Path]) -> None:
        """
        Discover package directories (those containing __init__.py).
        
        Builds a hierarchical package structure.
        """
        # Find all directories containing __init__.py
        package_dirs: set[Path] = set()
        for file_path in files:
            if file_path.name == "__init__.py":
                package_dirs.add(file_path.parent)
        
        # Also add parent directories that are packages
        for pkg_dir in list(package_dirs):
            parent = pkg_dir.parent
            while parent >= self.root:
                if (parent / "__init__.py").exists():
                    package_dirs.add(parent)
                parent = parent.parent
        
        # Sort by depth (shallowest first) to build hierarchy correctly
        sorted_dirs = sorted(package_dirs, key=lambda p: len(p.parts))
        
        for pkg_dir in sorted_dirs:
            rel_path = self._get_relative_path(pkg_dir)
            pkg_name = pkg_dir.name
            
            # Calculate qualified name
            if rel_path == ".":
                qualified_name = pkg_name
            else:
                qualified_name = rel_path.replace("/", ".").replace("\\", ".")
            
            # Find parent package
            parent_id = ""
            parent_dir = pkg_dir.parent
            if parent_dir >= self.root:
                parent_rel = self._get_relative_path(parent_dir)
                if parent_rel in self._package_map:
                    parent_id = parent_rel
            
            # Extract docstring from __init__.py if it exists
            init_path = pkg_dir / "__init__.py"
            docstring = None
            if init_path.exists():
                try:
                    content = init_path.read_bytes()
                    tree = self.parser.parse(content)
                    docstring = self._extract_docstring(tree.root_node, content)
                except Exception:
                    pass
            
            package = PackageInfo(
                id=rel_path if rel_path != "." else pkg_name,
                path=pkg_dir,
                name=pkg_name,
                qualified_name=qualified_name,
                parent_id=parent_id,
                docstring=docstring,
            )
            
            self.packages.append(package)
            self._package_map[rel_path] = package
            
            # Register in symbol table
            self.symbols[package.id] = SymbolEntry(
                id=package.id,
                name=pkg_name,
                kind="package",
                file_path=pkg_dir,
                qualified_name=qualified_name,
            )
            self.qualified_to_id[qualified_name] = package.id
            
            # Update parent's child list
            if parent_id and parent_id in self._package_map:
                self._package_map[parent_id].child_packages.append(package.id)
    
    def _get_text(self, node: Node, content: bytes) -> str:
        """Extract text from a node."""
        return content[node.start_byte:node.end_byte].decode("utf-8", errors="replace")
    
    def _get_location(self, node: Node) -> SourceLocation:
        """Extract location from a node."""
        return SourceLocation(
            line=node.start_point[0] + 1,
            column=node.start_point[1],
            end_line=node.end_point[0] + 1,
            end_column=node.end_point[1],
            start_byte=node.start_byte,
            end_byte=node.end_byte,
        )
    
    # =========================================================================
    # Pass 1: Discovery
    # =========================================================================
    
    def _pass1_discovery(self, files: list[Path]) -> None:
        """
        Build initial mapping of file paths to module IDs.
        
        Creates a SymbolEntry for each module (file).
        """
        for file_path in files:
            file_id = self._get_relative_path(file_path)
            module_name, package = self._path_to_module_name(file_path)
            qualified_name = f"{package}.{module_name}" if package else module_name
            
            entry = SymbolEntry(
                id=file_id,
                name=module_name,
                kind="module",
                file_path=file_path,
                qualified_name=qualified_name,
            )
            
            self.symbols[file_id] = entry
            self.qualified_to_id[qualified_name] = file_id
            
            # Link module to parent package
            parent_dir = file_path.parent
            parent_rel = self._get_relative_path(parent_dir)
            if parent_rel in self._package_map:
                # Skip __init__.py modules as they are part of the package itself
                if file_path.name != "__init__.py":
                    self._package_map[parent_rel].child_modules.append(file_id)
    
    # =========================================================================
    # Pass 2: Local AST Extraction
    # =========================================================================
    
    def _pass2_local_ast(self, files: list[Path]) -> None:
        """
        Parse each file and extract definitions + references.
        """
        for i, file_path in enumerate(files):
            try:
                self._parse_file(file_path)
                if (i + 1) % 50 == 0:
                    self.log.info("parsing_progress", completed=i + 1, total=len(files))
            except Exception as e:
                error_msg = f"{file_path}: {e}"
                self.errors.append(error_msg)
                self.log.warning("parse_error", path=str(file_path), error=str(e))
    
    def _parse_file(self, file_path: Path) -> None:
        """Parse a single file and extract all information."""
        content = file_path.read_bytes()
        tree = self.parser.parse(content)
        
        file_id = self._get_relative_path(file_path)
        module_name, package = self._path_to_module_name(file_path)
        
        # Create module info
        module = ModuleInfo(
            id=file_id,
            path=file_path,
            name=module_name,
            package=package,
            lines_of_code=content.count(b"\n") + 1,
        )
        
        # Extract module docstring
        module.docstring = self._extract_docstring(tree.root_node, content)
        
        # Extract imports first (needed for reference resolution)
        self._extract_imports(tree.root_node, content, module)
        
        # Extract definitions (classes, functions, variables)
        self._extract_definitions(tree.root_node, content, module, file_id)
        
        # Extract references within functions
        self._extract_references(tree.root_node, content, module, file_id)
        
        self.modules.append(module)
    
    def _extract_docstring(self, root: Node, content: bytes) -> str | None:
        """Extract module-level docstring if present."""
        for child in root.children:
            if child.type == "expression_statement":
                expr = child.children[0] if child.children else None
                if expr and expr.type == "string":
                    text = self._get_text(expr, content)
                    # Remove quotes
                    if text.startswith('"""') or text.startswith("'''"):
                        return text[3:-3].strip()
                    elif text.startswith('"') or text.startswith("'"):
                        return text[1:-1].strip()
            elif child.type not in ("comment",):
                break
        return None
    
    def _extract_imports(self, root: Node, content: bytes, module: ModuleInfo) -> None:
        """Extract and register all imports in the file."""
        file_id = module.id
        
        for child in root.children:
            if child.type == "import_statement":
                self._parse_import_statement(child, content, module, file_id)
            elif child.type == "import_from_statement":
                self._parse_from_import(child, content, module, file_id)
    
    def _parse_import_statement(
        self, node: Node, content: bytes, module: ModuleInfo, file_id: str
    ) -> None:
        """Parse 'import x, y as z' statement."""
        for child in node.children:
            if child.type == "dotted_name":
                module_name = self._get_text(child, content)
                alias = module_name.split(".")[-1]
                
                imp = ImportInfo(
                    id=f"{file_id}::import::{module_name}",
                    module_name=module_name,
                    location=self._get_location(child),
                )
                module.imports.append(imp)
                
                # Register import for resolution
                self.file_imports[file_id][alias] = ImportEntry(
                    alias=alias,
                    qualified_name=module_name,
                    target_id="",  # Resolved in pass 3
                )
                
            elif child.type == "aliased_import":
                name_node = child.child_by_field_name("name")
                alias_node = child.child_by_field_name("alias")
                
                if name_node and alias_node:
                    module_name = self._get_text(name_node, content)
                    alias = self._get_text(alias_node, content)
                    
                    imp = ImportInfo(
                        id=f"{file_id}::import::{module_name}",
                        module_name=module_name,
                        aliases={module_name: alias},
                        location=self._get_location(child),
                    )
                    module.imports.append(imp)
                    
                    self.file_imports[file_id][alias] = ImportEntry(
                        alias=alias,
                        qualified_name=module_name,
                        target_id="",
                    )
    
    def _parse_from_import(
        self, node: Node, content: bytes, module: ModuleInfo, file_id: str
    ) -> None:
        """Parse 'from x import y, z' statement."""
        module_name = ""
        relative_level = 0
        imported_names: list[str] = []
        aliases: dict[str, str] = {}
        
        for child in node.children:
            if child.type == "dotted_name":
                module_name = self._get_text(child, content)
            elif child.type == "relative_import":
                # Count dots for relative level
                rel_text = self._get_text(child, content)
                relative_level = len(rel_text) - len(rel_text.lstrip("."))
                remaining = rel_text.lstrip(".")
                if remaining:
                    module_name = remaining
            elif child.type == "import_prefix":
                # Dots at the start
                dot_text = self._get_text(child, content)
                relative_level = dot_text.count(".")
        
        # Get imported names
        for child in node.children:
            if child.type == "dotted_name" and child.prev_sibling:
                # This is an imported name (after 'import')
                if child.prev_sibling.type in ("import", ","):
                    name = self._get_text(child, content)
                    imported_names.append(name)
            elif child.type == "aliased_import":
                name_node = child.child_by_field_name("name")
                alias_node = child.child_by_field_name("alias")
                if name_node:
                    name = self._get_text(name_node, content)
                    imported_names.append(name)
                    if alias_node:
                        alias = self._get_text(alias_node, content)
                        aliases[name] = alias
        
        # Handle wildcard import
        for child in node.children:
            if child.type == "wildcard_import":
                imported_names.append("*")
        
        # Resolve relative imports
        resolved_module = module_name
        if relative_level > 0:
            resolved_module = self._resolve_relative_import(
                module.package, module_name, relative_level
            )
        
        imp = ImportInfo(
            id=f"{file_id}::import::{resolved_module or module_name}",
            module_name=module_name,
            imported_names=imported_names,
            aliases=aliases,
            is_relative=relative_level > 0,
            relative_level=relative_level,
            resolved_module=resolved_module,
            location=self._get_location(node),
        )
        module.imports.append(imp)
        
        # Register each imported name
        for name in imported_names:
            actual_alias = aliases.get(name, name)
            full_qualified = f"{resolved_module}.{name}" if resolved_module else name
            
            self.file_imports[file_id][actual_alias] = ImportEntry(
                alias=actual_alias,
                qualified_name=full_qualified,
                target_id="",
                imported_names=[name],
            )
    
    def _resolve_relative_import(
        self, current_package: str, module_name: str, relative_level: int
    ) -> str:
        """Resolve a relative import to absolute module path."""
        if not current_package:
            return module_name
        
        parts = current_package.split(".")
        
        # Go up n-1 levels (one dot means current package)
        if relative_level > len(parts):
            return module_name
        
        base_parts = parts[: len(parts) - relative_level + 1]
        base = ".".join(base_parts)
        
        if module_name:
            return f"{base}.{module_name}"
        return base
    
    def _extract_definitions(
        self, root: Node, content: bytes, module: ModuleInfo, file_id: str
    ) -> None:
        """Extract class, function, and variable definitions."""
        self._extract_from_block(
            root, content, module, file_id, parent_qualified=""
        )
    
    def _extract_from_block(
        self,
        node: Node,
        content: bytes,
        module: ModuleInfo,
        file_id: str,
        parent_qualified: str,
        parent_class: ClassInfo | None = None,
    ) -> None:
        """Recursively extract definitions from a block."""
        pending_decorators: list[DecoratorInfo] = []
        
        for child in node.children:
            if child.type == "decorator":
                dec = self._parse_decorator(child, content)
                if dec:
                    pending_decorators.append(dec)
                    
            elif child.type == "decorated_definition":
                # Get decorators and the actual definition
                decs = []
                target = None
                for sub in child.children:
                    if sub.type == "decorator":
                        dec = self._parse_decorator(sub, content)
                        if dec:
                            decs.append(dec)
                    else:
                        target = sub
                
                if target:
                    self._process_definition(
                        target, content, module, file_id, 
                        parent_qualified, parent_class, decs
                    )
                pending_decorators = []
                
            elif child.type in ("function_definition", "class_definition"):
                self._process_definition(
                    child, content, module, file_id,
                    parent_qualified, parent_class, pending_decorators
                )
                pending_decorators = []
                
            elif child.type == "expression_statement":
                # Check for variable assignment
                for sub in child.children:
                    if sub.type == "assignment":
                        var = self._parse_variable(sub, content, file_id, parent_qualified)
                        if var:
                            if parent_class:
                                var.scope = "class"
                                parent_class.class_variables.append(var)
                            else:
                                var.scope = "module"
                                module.variables.append(var)
                            
                            # Register in symbol table
                            self.symbols[var.id] = SymbolEntry(
                                id=var.id,
                                name=var.name,
                                kind="variable",
                                file_path=module.path,
                                qualified_name=f"{parent_qualified}.{var.name}" if parent_qualified else var.name,
                                parent_id=file_id,
                                location=var.location,
                            )
    
    def _process_definition(
        self,
        node: Node,
        content: bytes,
        module: ModuleInfo,
        file_id: str,
        parent_qualified: str,
        parent_class: ClassInfo | None,
        decorators: list[DecoratorInfo],
    ) -> None:
        """Process a function or class definition."""
        if node.type == "function_definition":
            func = self._parse_function(
                node, content, file_id, parent_qualified, 
                is_method=parent_class is not None,
                decorators=decorators,
            )
            if func:
                if parent_class:
                    parent_class.methods.append(func)
                else:
                    module.functions.append(func)
                
                # Register in symbol table
                self.symbols[func.id] = SymbolEntry(
                    id=func.id,
                    name=func.name,
                    kind="method" if func.is_method else "function",
                    file_path=module.path,
                    qualified_name=func.qualified_name,
                    parent_id=parent_class.id if parent_class else file_id,
                    location=func.location,
                )
                self.qualified_to_id[func.qualified_name] = func.id
                
        elif node.type == "class_definition":
            cls = self._parse_class(
                node, content, file_id, parent_qualified, module, decorators
            )
            if cls:
                module.classes.append(cls)
                
                # Register in symbol table
                self.symbols[cls.id] = SymbolEntry(
                    id=cls.id,
                    name=cls.name,
                    kind="class",
                    file_path=module.path,
                    qualified_name=cls.qualified_name,
                    parent_id=file_id,
                    location=cls.location,
                )
                self.qualified_to_id[cls.qualified_name] = cls.id
    
    def _parse_decorator(self, node: Node, content: bytes) -> DecoratorInfo | None:
        """Parse a decorator node."""
        # Find the decorator name
        for child in node.children:
            if child.type == "identifier":
                return DecoratorInfo(
                    name=self._get_text(child, content),
                    location=self._get_location(node),
                )
            elif child.type == "call":
                # @decorator(args)
                func = child.child_by_field_name("function")
                if func:
                    args = []
                    args_node = child.child_by_field_name("arguments")
                    if args_node:
                        for arg in args_node.children:
                            if arg.type not in ("(", ")", ","):
                                args.append(self._get_text(arg, content))
                    return DecoratorInfo(
                        name=self._get_text(func, content),
                        arguments=args,
                        location=self._get_location(node),
                    )
            elif child.type == "attribute":
                # @module.decorator
                return DecoratorInfo(
                    name=self._get_text(child, content),
                    location=self._get_location(node),
                )
        return None
    
    def _parse_function(
        self,
        node: Node,
        content: bytes,
        file_id: str,
        parent_qualified: str,
        is_method: bool = False,
        decorators: list[DecoratorInfo] | None = None,
    ) -> FunctionInfo | None:
        """Parse a function definition."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None
        
        name = self._get_text(name_node, content)
        qualified_name = f"{parent_qualified}.{name}" if parent_qualified else name
        func_id = f"{file_id}::{name}" if not parent_qualified else f"{file_id}::{parent_qualified.split('.')[-1]}::{name}"
        
        # Parse parameters
        params = []
        params_node = node.child_by_field_name("parameters")
        if params_node:
            params = self._parse_parameters(params_node, content)
        
        # Parse return type
        return_type = None
        return_node = node.child_by_field_name("return_type")
        if return_node:
            return_type = self._get_text(return_node, content)
        
        # Check for async
        is_async = any(c.type == "async" for c in node.children)
        
        # Extract docstring from body
        docstring = None
        body_node = node.child_by_field_name("body")
        if body_node:
            docstring = self._extract_block_docstring(body_node, content)
        
        # Determine method type from decorators
        is_classmethod = False
        is_staticmethod = False
        is_property = False
        if decorators:
            for dec in decorators:
                if dec.name == "classmethod":
                    is_classmethod = True
                elif dec.name == "staticmethod":
                    is_staticmethod = True
                elif dec.name == "property":
                    is_property = True
        
        # Extract function calls
        calls = []
        if body_node:
            calls = self._extract_calls_from_block(body_node, content)
        
        return FunctionInfo(
            id=func_id,
            name=name,
            qualified_name=qualified_name,
            parameters=params,
            return_type=return_type,
            decorators=decorators or [],
            docstring=docstring,
            is_async=is_async,
            is_method=is_method,
            is_classmethod=is_classmethod,
            is_staticmethod=is_staticmethod,
            is_property=is_property,
            location=self._get_location(node),
            calls=calls,
            complexity=self._calculate_complexity(body_node) if body_node else 1,
        )
    
    def _parse_parameters(self, node: Node, content: bytes) -> list[ParameterInfo]:
        """Parse function parameters."""
        params = []
        
        for child in node.children:
            if child.type in ("identifier", "typed_parameter", "default_parameter",
                             "typed_default_parameter", "list_splat_pattern",
                             "dictionary_splat_pattern"):
                param = self._parse_single_parameter(child, content)
                if param:
                    params.append(param)
        
        return params
    
    def _parse_single_parameter(self, node: Node, content: bytes) -> ParameterInfo | None:
        """Parse a single parameter."""
        name = ""
        type_hint = None
        default_value = None
        is_args = False
        is_kwargs = False
        
        if node.type == "identifier":
            name = self._get_text(node, content)
        elif node.type == "typed_parameter":
            name_node = node.child_by_field_name("name") or node.children[0]
            name = self._get_text(name_node, content)
            type_node = node.child_by_field_name("type")
            if type_node:
                type_hint = self._get_text(type_node, content)
        elif node.type == "default_parameter":
            name_node = node.child_by_field_name("name") or node.children[0]
            name = self._get_text(name_node, content)
            value_node = node.child_by_field_name("value")
            if value_node:
                default_value = self._get_text(value_node, content)
        elif node.type == "typed_default_parameter":
            name_node = node.child_by_field_name("name") or node.children[0]
            name = self._get_text(name_node, content)
            type_node = node.child_by_field_name("type")
            if type_node:
                type_hint = self._get_text(type_node, content)
            value_node = node.child_by_field_name("value")
            if value_node:
                default_value = self._get_text(value_node, content)
        elif node.type == "list_splat_pattern":
            for child in node.children:
                if child.type == "identifier":
                    name = self._get_text(child, content)
                    is_args = True
                    break
        elif node.type == "dictionary_splat_pattern":
            for child in node.children:
                if child.type == "identifier":
                    name = self._get_text(child, content)
                    is_kwargs = True
                    break
        
        if not name or name in ("self", "cls"):
            return None
        
        return ParameterInfo(
            name=name,
            type_hint=type_hint,
            default_value=default_value,
            is_args=is_args,
            is_kwargs=is_kwargs,
        )
    
    def _parse_class(
        self,
        node: Node,
        content: bytes,
        file_id: str,
        parent_qualified: str,
        module: ModuleInfo,
        decorators: list[DecoratorInfo] | None = None,
    ) -> ClassInfo | None:
        """Parse a class definition."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None
        
        name = self._get_text(name_node, content)
        qualified_name = f"{module.qualified_name}.{name}"
        class_id = f"{file_id}::{name}"
        
        # Parse base classes
        bases = []
        bases_node = node.child_by_field_name("superclasses")
        if bases_node:
            for child in bases_node.children:
                if child.type in ("identifier", "attribute"):
                    bases.append(self._get_text(child, content))
        
        # Check for abstractness
        is_abstract = any(
            d.name in ("abstractmethod", "ABC", "ABCMeta") 
            for d in (decorators or [])
        ) or any(b in ("ABC", "ABCMeta") for b in bases)
        
        cls = ClassInfo(
            id=class_id,
            name=name,
            qualified_name=qualified_name,
            bases=bases,
            decorators=decorators or [],
            is_abstract=is_abstract,
            location=self._get_location(node),
        )
        
        # Parse class body
        body_node = node.child_by_field_name("body")
        if body_node:
            # Extract docstring
            cls.docstring = self._extract_block_docstring(body_node, content)
            
            # Extract methods and class variables
            self._extract_from_block(
                body_node, content, module, file_id,
                parent_qualified=qualified_name,
                parent_class=cls,
            )
        
        return cls
    
    def _parse_variable(
        self, node: Node, content: bytes, file_id: str, parent_qualified: str
    ) -> VariableInfo | None:
        """Parse a variable assignment."""
        left_node = node.child_by_field_name("left")
        if not left_node or left_node.type != "identifier":
            return None
        
        name = self._get_text(left_node, content)
        if name.startswith("_") and not name.startswith("__"):
            # Skip private variables
            pass
        
        # Get initial value
        right_node = node.child_by_field_name("right")
        initial_value = self._get_text(right_node, content)[:100] if right_node else None
        
        # Check for type annotation
        type_node = node.child_by_field_name("type")
        type_hint = self._get_text(type_node, content) if type_node else None
        
        var_id = f"{file_id}::{name}" if not parent_qualified else f"{file_id}::{parent_qualified.split('.')[-1]}::{name}"
        
        return VariableInfo(
            id=var_id,
            name=name,
            type_hint=type_hint,
            initial_value=initial_value,
            is_constant=name.isupper(),
            location=self._get_location(node),
        )
    
    def _extract_block_docstring(self, block: Node, content: bytes) -> str | None:
        """Extract docstring from a block."""
        for child in block.children:
            if child.type == "expression_statement":
                expr = child.children[0] if child.children else None
                if expr and expr.type == "string":
                    text = self._get_text(expr, content)
                    if text.startswith('"""') or text.startswith("'''"):
                        return text[3:-3].strip()
                    elif text.startswith('"') or text.startswith("'"):
                        return text[1:-1].strip()
            elif child.type not in ("comment", "pass_statement"):
                break
        return None
    
    def _extract_calls_from_block(self, block: Node, content: bytes) -> list[str]:
        """Extract function call names from a block."""
        calls = []
        
        def walk(node: Node) -> None:
            if node.type == "call":
                func_node = node.child_by_field_name("function")
                if func_node:
                    if func_node.type == "identifier":
                        calls.append(self._get_text(func_node, content))
                    elif func_node.type == "attribute":
                        calls.append(self._get_text(func_node, content))
            
            for child in node.children:
                walk(child)
        
        walk(block)
        return calls
    
    def _calculate_complexity(self, block: Node) -> int:
        """Calculate cyclomatic complexity of a block."""
        complexity = 1
        decision_types = {
            "if_statement", "elif_clause", "for_statement", 
            "while_statement", "except_clause", "with_statement",
            "and", "or", "conditional_expression",
        }
        
        def walk(node: Node) -> None:
            nonlocal complexity
            if node.type in decision_types:
                complexity += 1
            for child in node.children:
                walk(child)
        
        walk(block)
        return complexity
    
    def _extract_references(
        self, root: Node, content: bytes, module: ModuleInfo, file_id: str
    ) -> None:
        """Extract symbol references from functions."""
        for func in module.functions:
            if func.location:
                # Find the function node in the tree
                func_refs = self._extract_refs_in_range(
                    root, content, 
                    func.location.start_byte, func.location.end_byte,
                    func.id
                )
                func.references = func_refs
        
        for cls in module.classes:
            for method in cls.methods:
                if method.location:
                    method_refs = self._extract_refs_in_range(
                        root, content,
                        method.location.start_byte, method.location.end_byte,
                        method.id
                    )
                    method.references = method_refs
    
    def _extract_refs_in_range(
        self, root: Node, content: bytes, 
        start_byte: int, end_byte: int, context_id: str
    ) -> list[SymbolReference]:
        """Extract references within a byte range."""
        refs = []
        
        def walk(node: Node) -> None:
            if node.start_byte < start_byte or node.end_byte > end_byte:
                for child in node.children:
                    if child.end_byte > start_byte and child.start_byte < end_byte:
                        walk(child)
                return
            
            if node.type == "call":
                func_node = node.child_by_field_name("function")
                if func_node:
                    name = self._get_text(func_node, content)
                    refs.append(SymbolReference(
                        name=name,
                        ref_type="call",
                        location=self._get_location(func_node),
                        context_id=context_id,
                    ))
            
            for child in node.children:
                walk(child)
        
        walk(root)
        return refs
    
    # =========================================================================
    # Pass 3: Linker
    # =========================================================================
    
    def _pass3_linker(self) -> None:
        """
        Resolve cross-file references and create relationships.
        """
        # Create package hierarchy relationships
        self._create_package_relationships()
        
        for module in self.modules:
            file_id = module.id
            
            # Create CONTAINS relationships
            self._create_contains_relationships(module, file_id)
            
            # Resolve import relationships  
            self._resolve_imports(module, file_id)
            
            # Resolve function calls
            self._resolve_calls(module, file_id)
            
            # Resolve inheritance
            self._resolve_inheritance(module, file_id)
    
    def _create_package_relationships(self) -> None:
        """Create CONTAINS relationships for package hierarchy."""
        for package in self.packages:
            # Package -> child packages
            for child_pkg_id in package.child_packages:
                self.relationships.append(Relationship(
                    source_id=package.id,
                    target_id=child_pkg_id,
                    relationship_type=RelationshipType.CONTAINS,
                ))
            
            # Package -> child modules
            for child_mod_id in package.child_modules:
                self.relationships.append(Relationship(
                    source_id=package.id,
                    target_id=child_mod_id,
                    relationship_type=RelationshipType.CONTAINS,
                ))
    
    def _create_contains_relationships(self, module: ModuleInfo, file_id: str) -> None:
        """Create CONTAINS relationships for module structure."""
        # Module contains classes
        for cls in module.classes:
            self.relationships.append(Relationship(
                source_id=file_id,
                target_id=cls.id,
                relationship_type=RelationshipType.CONTAINS,
            ))
            
            # Class contains methods
            for method in cls.methods:
                self.relationships.append(Relationship(
                    source_id=cls.id,
                    target_id=method.id,
                    relationship_type=RelationshipType.CONTAINS,
                ))
            
            # Class contains variables
            for var in cls.all_variables:
                self.relationships.append(Relationship(
                    source_id=cls.id,
                    target_id=var.id,
                    relationship_type=RelationshipType.DEFINES,
                ))
        
        # Module contains functions
        for func in module.functions:
            self.relationships.append(Relationship(
                source_id=file_id,
                target_id=func.id,
                relationship_type=RelationshipType.CONTAINS,
            ))
        
        # Module contains variables
        for var in module.variables:
            self.relationships.append(Relationship(
                source_id=file_id,
                target_id=var.id,
                relationship_type=RelationshipType.DEFINES,
            ))
    
    def _resolve_imports(self, module: ModuleInfo, file_id: str) -> None:
        """Resolve and create import relationships."""
        for imp in module.imports:
            target_module = imp.resolved_module or imp.module_name
            target_id = self.qualified_to_id.get(target_module)
            
            if target_id:
                self.relationships.append(Relationship(
                    source_id=file_id,
                    target_id=target_id,
                    relationship_type=RelationshipType.IMPORTS,
                    properties={
                        "imported_names": imp.imported_names,
                        "is_relative": imp.is_relative,
                    },
                ))
                
                # Update import entry with resolved ID
                for alias, entry in self.file_imports[file_id].items():
                    if entry.qualified_name.startswith(target_module):
                        entry.target_id = target_id
                
                # Create edges for specific imported symbols
                for name in imp.imported_names:
                    if name == "*":
                        continue
                    
                    symbol_qualified = f"{target_module}.{name}"
                    symbol_id = self.qualified_to_id.get(symbol_qualified)
                    
                    if symbol_id:
                        self.relationships.append(Relationship(
                            source_id=file_id,
                            target_id=symbol_id,
                            relationship_type=RelationshipType.IMPORTS,
                            properties={"symbol_name": name},
                        ))
    
    def _resolve_calls(self, module: ModuleInfo, file_id: str) -> None:
        """Resolve function calls to their definitions."""
        imports = self.file_imports.get(file_id, {})
        
        for func in module.functions:
            self._resolve_function_calls(func, file_id, imports, module)
        
        for cls in module.classes:
            for method in cls.methods:
                self._resolve_function_calls(method, file_id, imports, module, cls)
    
    def _resolve_function_calls(
        self,
        func: FunctionInfo,
        file_id: str,
        imports: dict[str, ImportEntry],
        module: ModuleInfo,
        parent_class: ClassInfo | None = None,
    ) -> None:
        """Resolve calls within a function."""
        for call_name in func.calls:
            target_id = self._resolve_symbol(
                call_name, file_id, imports, module, parent_class
            )
            
            if target_id:
                self.relationships.append(Relationship(
                    source_id=func.id,
                    target_id=target_id,
                    relationship_type=RelationshipType.CALLS,
                    properties={"call_name": call_name},
                ))
    
    def _resolve_symbol(
        self,
        name: str,
        file_id: str,
        imports: dict[str, ImportEntry],
        module: ModuleInfo,
        parent_class: ClassInfo | None = None,
    ) -> str | None:
        """
        Resolve a symbol name to its definition ID.
        
        Resolution order:
        1. Class scope (if in a method)
        2. Module scope
        3. Imported symbols
        4. Builtins (not tracked)
        """
        # Handle attribute access (x.y.z)
        if "." in name:
            parts = name.split(".")
            first_part = parts[0]
            
            # Check if first part is an import alias
            if first_part in imports:
                import_entry = imports[first_part]
                # Build full qualified name
                rest = ".".join(parts[1:])
                full_qualified = f"{import_entry.qualified_name.rsplit('.', 1)[0]}.{rest}" if import_entry.imported_names else f"{import_entry.qualified_name}.{rest}"
                
                target_id = self.qualified_to_id.get(full_qualified)
                if target_id:
                    return target_id
            
            # Check if first part is self/cls
            if first_part in ("self", "cls") and parent_class:
                method_name = parts[1] if len(parts) > 1 else None
                if method_name:
                    target_id = f"{file_id}::{parent_class.name}::{method_name}"
                    if target_id in self.symbols:
                        return target_id
        
        # Check class methods (if in a method)
        if parent_class:
            method_id = f"{file_id}::{parent_class.name}::{name}"
            if method_id in self.symbols:
                return method_id
        
        # Check module-level functions
        func_id = f"{file_id}::{name}"
        if func_id in self.symbols:
            return func_id
        
        # Check imports
        if name in imports:
            import_entry = imports[name]
            target_id = self.qualified_to_id.get(import_entry.qualified_name)
            if target_id:
                return target_id
            
            # Try to resolve the target
            target_id = import_entry.target_id
            if target_id:
                # Build symbol ID within target module
                symbol_id = f"{target_id}::{name}"
                if symbol_id in self.symbols:
                    return symbol_id
        
        # Check qualified name directly
        if name in self.qualified_to_id:
            return self.qualified_to_id[name]
        
        return None
    
    def _resolve_inheritance(self, module: ModuleInfo, file_id: str) -> None:
        """Resolve class inheritance relationships."""
        imports = self.file_imports.get(file_id, {})
        
        for cls in module.classes:
            for base in cls.bases:
                target_id = self._resolve_symbol(
                    base, file_id, imports, module
                )
                
                if target_id:
                    cls.resolved_bases.append(target_id)
                    self.relationships.append(Relationship(
                        source_id=cls.id,
                        target_id=target_id,
                        relationship_type=RelationshipType.INHERITS,
                        properties={"base_name": base},
                    ))
