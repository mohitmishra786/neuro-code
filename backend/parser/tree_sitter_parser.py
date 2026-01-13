"""
NeuroCode Tree-sitter Parser.

Fast, incremental parsing of Python source files using Tree-sitter.
Requires Python 3.11+.
"""

import time
from pathlib import Path
from typing import Iterator

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Node, Tree

from parser.models import (
    ClassInfo,
    DecoratorInfo,
    FunctionInfo,
    ImportInfo,
    ModuleInfo,
    ParameterInfo,
    SourceLocation,
    VariableInfo,
)
from utils.logger import LoggerMixin


class TreeSitterParser(LoggerMixin):
    """
    Fast Python parser using Tree-sitter.

    Provides incremental parsing, error tolerance, and detailed AST extraction.
    """

    def __init__(self) -> None:
        """Initialize the Tree-sitter parser with Python language."""
        self._language = Language(tspython.language())
        self._parser = Parser(self._language)
        self._source: bytes = b""
        self._tree: Tree | None = None

    def parse_file(self, file_path: Path) -> ModuleInfo:
        """
        Parse a Python file and extract all code elements.

        Args:
            file_path: Path to the Python file

        Returns:
            ModuleInfo containing all parsed elements
        """
        start_time = time.perf_counter()

        try:
            content = file_path.read_bytes()
        except OSError as e:
            self.log.error("failed_to_read_file", path=str(file_path), error=str(e))
            return ModuleInfo(path=file_path, name=file_path.stem)

        module = self.parse_content(content, file_path)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        self.log.debug(
            "parsed_file",
            path=str(file_path),
            elapsed_ms=round(elapsed_ms, 2),
            classes=len(module.classes),
            functions=len(module.functions),
        )
        return module

    def parse_content(self, content: bytes, file_path: Path | None = None) -> ModuleInfo:
        """
        Parse Python content and extract all code elements.

        Args:
            content: Python source code as bytes
            file_path: Optional path for the module

        Returns:
            ModuleInfo containing all parsed elements
        """
        self._source = content
        self._tree = self._parser.parse(content)

        if self._tree is None:
            self.log.error("parse_failed", path=str(file_path) if file_path else "<memory>")
            return ModuleInfo(path=file_path or Path(), name=file_path.stem if file_path else "")

        root = self._tree.root_node
        module = ModuleInfo(
            path=file_path or Path(),
            name=file_path.stem if file_path else "",
            lines_of_code=content.count(b"\n") + 1,
        )

        # Extract module docstring
        module.docstring = self._extract_module_docstring(root)

        # Extract all elements from the module body
        for child in root.children:
            if child.type == "import_statement":
                module.imports.append(self._parse_import(child))
            elif child.type == "import_from_statement":
                module.imports.append(self._parse_from_import(child))
            elif child.type == "class_definition":
                module.classes.append(self._parse_class(child, module.name))
            elif child.type == "function_definition":
                module.functions.append(self._parse_function(child, module.name))
            elif child.type == "decorated_definition":
                decorated = self._parse_decorated(child, module.name)
                if isinstance(decorated, ClassInfo):
                    module.classes.append(decorated)
                elif isinstance(decorated, FunctionInfo):
                    module.functions.append(decorated)
            elif child.type == "expression_statement":
                var = self._parse_module_variable(child)
                if var:
                    module.variables.append(var)

        return module

    def parse_incremental(self, content: bytes, old_tree: Tree) -> Tree:
        """
        Perform incremental parsing for efficiency on file changes.

        Args:
            content: Updated Python source code
            old_tree: Previous parse tree

        Returns:
            Updated parse tree
        """
        self._source = content
        self._tree = self._parser.parse(content, old_tree)
        return self._tree

    def _get_text(self, node: Node) -> str:
        """Extract text content from a node."""
        return self._source[node.start_byte : node.end_byte].decode("utf-8")

    def _get_location(self, node: Node) -> SourceLocation:
        """Extract source location from a node."""
        return SourceLocation(
            line=node.start_point[0] + 1,  # 1-indexed
            column=node.start_point[1],
            end_line=node.end_point[0] + 1,
            end_column=node.end_point[1],
        )

    def _extract_module_docstring(self, root: Node) -> str | None:
        """Extract module-level docstring if present."""
        for child in root.children:
            if child.type == "expression_statement":
                expr = child.children[0] if child.children else None
                if expr and expr.type == "string":
                    docstring = self._get_text(expr)
                    return self._clean_docstring(docstring)
            elif child.type not in ("comment", "newline"):
                # First non-comment/newline statement is not a docstring
                break
        return None

    def _clean_docstring(self, docstring: str) -> str:
        """Remove quotes from docstring."""
        if docstring.startswith('"""') or docstring.startswith("'''"):
            return docstring[3:-3].strip()
        elif docstring.startswith('"') or docstring.startswith("'"):
            return docstring[1:-1].strip()
        return docstring.strip()

    def _parse_import(self, node: Node) -> ImportInfo:
        """Parse an import statement (import x, y, z)."""
        info = ImportInfo(location=self._get_location(node))

        for child in node.children:
            if child.type == "dotted_name":
                info.module_name = self._get_text(child)
            elif child.type == "aliased_import":
                name_node = child.child_by_field_name("name")
                alias_node = child.child_by_field_name("alias")
                if name_node:
                    name = self._get_text(name_node)
                    if alias_node:
                        info.aliases[name] = self._get_text(alias_node)
                    info.imported_names.append(name)

        return info

    def _parse_from_import(self, node: Node) -> ImportInfo:
        """Parse a from-import statement (from x import y, z)."""
        info = ImportInfo(location=self._get_location(node))

        for child in node.children:
            if child.type == "dotted_name":
                info.module_name = self._get_text(child)
            elif child.type == "relative_import":
                # Count dots for relative level
                for sub in child.children:
                    if sub.type == "import_prefix":
                        info.relative_level = self._get_text(sub).count(".")
                        info.is_relative = True
                    elif sub.type == "dotted_name":
                        info.module_name = self._get_text(sub)
            elif child.type == "import_prefix":
                info.relative_level = self._get_text(child).count(".")
                info.is_relative = True
            elif child.type in ("identifier", "dotted_name") and info.module_name:
                # This is an imported name
                info.imported_names.append(self._get_text(child))
            elif child.type == "aliased_import":
                name_node = child.child_by_field_name("name")
                alias_node = child.child_by_field_name("alias")
                if name_node:
                    name = self._get_text(name_node)
                    if alias_node:
                        info.aliases[name] = self._get_text(alias_node)
                    info.imported_names.append(name)
            elif child.type == "wildcard_import":
                info.imported_names.append("*")

        return info

    def _parse_class(
        self, node: Node, parent_qualified_name: str, decorators: list[DecoratorInfo] | None = None
    ) -> ClassInfo:
        """Parse a class definition."""
        info = ClassInfo(
            location=self._get_location(node),
            decorators=decorators or [],
        )

        for child in node.children:
            if child.type == "identifier":
                info.name = self._get_text(child)
                info.qualified_name = f"{parent_qualified_name}.{info.name}" if parent_qualified_name else info.name
            elif child.type == "argument_list":
                # Class bases
                info.bases = self._parse_class_bases(child)
            elif child.type == "block":
                self._parse_class_body(child, info)

        # Check if abstract
        info.is_abstract = any(
            d.name in ("abstractmethod", "ABC", "ABCMeta") for d in info.decorators
        ) or "ABC" in info.bases or "ABCMeta" in info.bases

        return info

    def _parse_class_bases(self, node: Node) -> list[str]:
        """Parse class base classes from argument list."""
        bases: list[str] = []
        for child in node.children:
            if child.type in ("identifier", "attribute"):
                bases.append(self._get_text(child))
            elif child.type == "keyword_argument":
                # metaclass= or other keyword args
                pass
        return bases

    def _parse_class_body(self, block: Node, info: ClassInfo) -> None:
        """Parse the body of a class definition."""
        first_statement = True

        for child in block.children:
            if child.type == "expression_statement":
                if first_statement:
                    # Check for docstring
                    expr = child.children[0] if child.children else None
                    if expr and expr.type == "string":
                        info.docstring = self._clean_docstring(self._get_text(expr))
                        first_statement = False
                        continue

                # Check for class variable
                var = self._parse_class_variable(child)
                if var:
                    info.class_variables.append(var)

            elif child.type == "function_definition":
                method = self._parse_function(child, info.qualified_name, is_method=True)
                info.methods.append(method)
                # Extract instance variables from __init__
                if method.name == "__init__":
                    info.instance_variables.extend(
                        self._extract_instance_variables(child, info.qualified_name)
                    )

            elif child.type == "decorated_definition":
                decorated = self._parse_decorated(child, info.qualified_name, is_method=True)
                if isinstance(decorated, FunctionInfo):
                    info.methods.append(decorated)
                elif isinstance(decorated, ClassInfo):
                    info.nested_classes.append(decorated)

            elif child.type == "class_definition":
                nested = self._parse_class(child, info.qualified_name)
                info.nested_classes.append(nested)

            first_statement = False

    def _parse_function(
        self,
        node: Node,
        parent_qualified_name: str,
        is_method: bool = False,
        decorators: list[DecoratorInfo] | None = None,
    ) -> FunctionInfo:
        """Parse a function or method definition."""
        info = FunctionInfo(
            location=self._get_location(node),
            is_method=is_method,
            decorators=decorators or [],
        )

        for child in node.children:
            if child.type == "identifier":
                info.name = self._get_text(child)
                info.qualified_name = f"{parent_qualified_name}.{info.name}" if parent_qualified_name else info.name
            elif child.type == "parameters":
                info.parameters = self._parse_parameters(child)
            elif child.type == "type":
                info.return_type = self._get_text(child)
            elif child.type == "block":
                info.docstring = self._extract_block_docstring(child)
                info.complexity = self._calculate_complexity(child)
                info.calls = self._extract_function_calls(child)
                info.variables = self._extract_local_variables(child)
                # Check for yield/yield from
                info.is_generator = self._has_yield(child)

        # Check for async
        if node.children and node.children[0].type == "async":
            info.is_async = True

        # Check decorator flags
        for decorator in info.decorators:
            if decorator.name == "classmethod":
                info.is_classmethod = True
            elif decorator.name == "staticmethod":
                info.is_staticmethod = True
            elif decorator.name == "property":
                info.is_property = True

        return info

    def _parse_parameters(self, node: Node) -> list[ParameterInfo]:
        """Parse function parameters."""
        params: list[ParameterInfo] = []

        for child in node.children:
            if child.type == "identifier":
                params.append(ParameterInfo(name=self._get_text(child)))
            elif child.type == "typed_parameter":
                name_node = child.child_by_field_name("name") or (
                    child.children[0] if child.children else None
                )
                type_node = child.child_by_field_name("type")
                if name_node:
                    params.append(
                        ParameterInfo(
                            name=self._get_text(name_node),
                            type_hint=self._get_text(type_node) if type_node else None,
                        )
                    )
            elif child.type == "default_parameter":
                name_node = child.child_by_field_name("name")
                value_node = child.child_by_field_name("value")
                if name_node:
                    params.append(
                        ParameterInfo(
                            name=self._get_text(name_node),
                            default_value=self._get_text(value_node) if value_node else None,
                        )
                    )
            elif child.type == "typed_default_parameter":
                name_node = child.child_by_field_name("name")
                type_node = child.child_by_field_name("type")
                value_node = child.child_by_field_name("value")
                if name_node:
                    params.append(
                        ParameterInfo(
                            name=self._get_text(name_node),
                            type_hint=self._get_text(type_node) if type_node else None,
                            default_value=self._get_text(value_node) if value_node else None,
                        )
                    )
            elif child.type == "list_splat_pattern":
                # *args
                name_node = child.children[0] if child.children else None
                if name_node:
                    params.append(
                        ParameterInfo(name=self._get_text(name_node), is_args=True)
                    )
            elif child.type == "dictionary_splat_pattern":
                # **kwargs
                name_node = child.children[0] if child.children else None
                if name_node:
                    params.append(
                        ParameterInfo(name=self._get_text(name_node), is_kwargs=True)
                    )

        return params

    def _parse_decorated(
        self, node: Node, parent_qualified_name: str, is_method: bool = False
    ) -> ClassInfo | FunctionInfo | None:
        """Parse a decorated definition (class or function with decorators)."""
        decorators: list[DecoratorInfo] = []

        for child in node.children:
            if child.type == "decorator":
                decorators.append(self._parse_decorator(child))
            elif child.type == "class_definition":
                return self._parse_class(child, parent_qualified_name, decorators)
            elif child.type == "function_definition":
                return self._parse_function(child, parent_qualified_name, is_method, decorators)

        return None

    def _parse_decorator(self, node: Node) -> DecoratorInfo:
        """Parse a decorator."""
        info = DecoratorInfo(name="", location=self._get_location(node))

        for child in node.children:
            if child.type in ("identifier", "attribute", "dotted_name"):
                info.name = self._get_text(child)
            elif child.type == "call":
                # Decorator with arguments @decorator(args)
                for sub in child.children:
                    if sub.type in ("identifier", "attribute"):
                        info.name = self._get_text(sub)
                    elif sub.type == "argument_list":
                        for arg in sub.children:
                            if arg.type not in ("(", ")", ","):
                                info.arguments.append(self._get_text(arg))

        return info

    def _parse_module_variable(self, node: Node) -> VariableInfo | None:
        """Parse a module-level variable assignment."""
        expr = node.children[0] if node.children else None
        if not expr or expr.type != "assignment":
            return None

        left = expr.child_by_field_name("left")
        right = expr.child_by_field_name("right")

        if not left or left.type != "identifier":
            return None

        name = self._get_text(left)
        value = self._get_text(right) if right else None

        return VariableInfo(
            name=name,
            initial_value=value,
            scope="module",
            is_constant=name.isupper(),
            location=self._get_location(node),
        )

    def _parse_class_variable(self, node: Node) -> VariableInfo | None:
        """Parse a class-level variable assignment."""
        expr = node.children[0] if node.children else None
        if not expr:
            return None

        if expr.type == "assignment":
            left = expr.child_by_field_name("left")
            right = expr.child_by_field_name("right")
            type_node = expr.child_by_field_name("type")

            if not left or left.type != "identifier":
                return None

            return VariableInfo(
                name=self._get_text(left),
                initial_value=self._get_text(right) if right else None,
                type_hint=self._get_text(type_node) if type_node else None,
                scope="class",
                is_constant=self._get_text(left).isupper(),
                location=self._get_location(node),
            )

        return None

    def _extract_instance_variables(self, init_node: Node, class_name: str) -> list[VariableInfo]:
        """Extract instance variables from __init__ method (self.x = ...)."""
        variables: list[VariableInfo] = []

        def walk(node: Node) -> None:
            if node.type == "assignment":
                left = node.child_by_field_name("left")
                right = node.child_by_field_name("right")

                if left and left.type == "attribute":
                    obj = left.child_by_field_name("object")
                    attr = left.child_by_field_name("attribute")

                    if obj and self._get_text(obj) == "self" and attr:
                        variables.append(
                            VariableInfo(
                                name=self._get_text(attr),
                                initial_value=self._get_text(right) if right else None,
                                scope="instance",
                                location=self._get_location(node),
                            )
                        )

            for child in node.children:
                walk(child)

        walk(init_node)
        return variables

    def _extract_block_docstring(self, block: Node) -> str | None:
        """Extract docstring from a block (first string expression)."""
        for child in block.children:
            if child.type == "expression_statement":
                expr = child.children[0] if child.children else None
                if expr and expr.type == "string":
                    return self._clean_docstring(self._get_text(expr))
            elif child.type not in ("comment", "newline"):
                break
        return None

    def _extract_local_variables(self, block: Node) -> list[VariableInfo]:
        """Extract local variable assignments from a function body."""
        variables: list[VariableInfo] = []
        seen_names: set[str] = set()

        def walk(node: Node) -> None:
            if node.type == "assignment":
                left = node.child_by_field_name("left")
                right = node.child_by_field_name("right")

                if left and left.type == "identifier":
                    name = self._get_text(left)
                    if name not in seen_names:
                        seen_names.add(name)
                        variables.append(
                            VariableInfo(
                                name=name,
                                initial_value=self._get_text(right) if right else None,
                                scope="function",
                                location=self._get_location(node),
                            )
                        )

            # Don't recurse into nested functions/classes
            if node.type not in ("function_definition", "class_definition"):
                for child in node.children:
                    walk(child)

        walk(block)
        return variables

    def _extract_function_calls(self, block: Node) -> list[str]:
        """Extract function calls from a block."""
        calls: list[str] = []

        def walk(node: Node) -> None:
            if node.type == "call":
                func = node.child_by_field_name("function")
                if func:
                    calls.append(self._get_text(func))

            # Don't recurse into nested functions/classes
            if node.type not in ("function_definition", "class_definition"):
                for child in node.children:
                    walk(child)

        walk(block)
        return calls

    def _calculate_complexity(self, block: Node) -> int:
        """Calculate cyclomatic complexity of a code block."""
        complexity = 1  # Base complexity

        decision_types = {
            "if_statement",
            "elif_clause",
            "for_statement",
            "while_statement",
            "except_clause",
            "with_statement",
            "assert_statement",
            "conditional_expression",  # ternary
        }

        boolean_ops = {"and", "or"}

        def walk(node: Node) -> None:
            nonlocal complexity

            if node.type in decision_types:
                complexity += 1
            elif node.type == "boolean_operator":
                op_node = node.children[1] if len(node.children) > 1 else None
                if op_node and self._get_text(op_node) in boolean_ops:
                    complexity += 1

            # Don't recurse into nested functions/classes
            if node.type not in ("function_definition", "class_definition"):
                for child in node.children:
                    walk(child)

        walk(block)
        return complexity

    def _has_yield(self, block: Node) -> bool:
        """Check if a block contains yield statements."""

        def walk(node: Node) -> bool:
            if node.type in ("yield", "yield_from"):
                return True

            # Don't recurse into nested functions
            if node.type != "function_definition":
                for child in node.children:
                    if walk(child):
                        return True

            return False

        return walk(block)
