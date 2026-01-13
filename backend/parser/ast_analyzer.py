"""
NeuroCode AST Analyzer.

Semantic analysis using Python's built-in ast module.
Complements Tree-sitter with deeper semantic understanding.
Requires Python 3.11+.
"""

import ast
from pathlib import Path
from typing import Any

from parser.models import (
    FunctionInfo,
    ClassInfo,
    ModuleInfo,
    VariableInfo,
    SourceLocation,
)
from utils.logger import LoggerMixin


class ASTAnalyzer(LoggerMixin):
    """
    Semantic analyzer using Python's built-in AST module.

    Provides deeper semantic analysis that Tree-sitter cannot offer,
    such as type inference hints, scope resolution, and control flow analysis.
    """

    def __init__(self) -> None:
        """Initialize the AST analyzer."""
        self._source: str = ""
        self._tree: ast.Module | None = None

    def analyze_file(self, file_path: Path) -> dict[str, Any]:
        """
        Perform semantic analysis on a Python file.

        Args:
            file_path: Path to the Python file

        Returns:
            Dictionary containing semantic analysis results
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            return self.analyze_content(content, str(file_path))
        except OSError as e:
            self.log.error("failed_to_read_file", path=str(file_path), error=str(e))
            return {"error": str(e)}

    def analyze_content(self, content: str, filename: str = "<string>") -> dict[str, Any]:
        """
        Perform semantic analysis on Python source code.

        Args:
            content: Python source code
            filename: Filename for error messages

        Returns:
            Dictionary containing semantic analysis results
        """
        self._source = content

        try:
            self._tree = ast.parse(content, filename=filename, type_comments=True)
        except SyntaxError as e:
            self.log.warning("syntax_error", filename=filename, error=str(e))
            return {"error": str(e), "syntax_error": True}

        return {
            "global_names": self._extract_global_names(),
            "type_annotations": self._extract_type_annotations(),
            "function_returns": self._analyze_function_returns(),
            "unused_imports": self._find_unused_imports(),
            "name_bindings": self._analyze_name_bindings(),
        }

    def enhance_module_info(self, module: ModuleInfo, file_path: Path) -> ModuleInfo:
        """
        Enhance a ModuleInfo with semantic analysis.

        Args:
            module: ModuleInfo from Tree-sitter parser
            file_path: Path to the Python file

        Returns:
            Enhanced ModuleInfo with semantic information
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            self._source = content
            self._tree = ast.parse(content, filename=str(file_path))
        except (OSError, SyntaxError) as e:
            self.log.warning("enhancement_failed", path=str(file_path), error=str(e))
            return module

        # Enhance functions with return type inference
        semantic_returns = self._analyze_function_returns()
        for func in module.functions:
            if func.name in semantic_returns and not func.return_type:
                func.return_type = semantic_returns[func.name].get("inferred_type")

        # Enhance classes with method resolution order info
        for cls in module.classes:
            mro = self._get_mro_info(cls.name)
            if mro:
                cls.bases = mro

        return module

    def _extract_global_names(self) -> set[str]:
        """Extract all globally defined names in the module."""
        if self._tree is None:
            return set()

        names: set[str] = set()

        for node in ast.walk(self._tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                names.add(node.name)
            elif isinstance(node, ast.ClassDef):
                names.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                names.add(node.target.id)

        return names

    def _extract_type_annotations(self) -> dict[str, str]:
        """Extract all type annotations from the module."""
        if self._tree is None:
            return {}

        annotations: dict[str, str] = {}

        for node in ast.walk(self._tree):
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                annotations[node.target.id] = ast.unparse(node.annotation)
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
                    if arg.annotation:
                        key = f"{node.name}.{arg.arg}"
                        annotations[key] = ast.unparse(arg.annotation)
                if node.returns:
                    annotations[f"{node.name}.__return__"] = ast.unparse(node.returns)

        return annotations

    def _analyze_function_returns(self) -> dict[str, dict[str, Any]]:
        """Analyze function return statements and infer types."""
        if self._tree is None:
            return {}

        results: dict[str, dict[str, Any]] = {}

        class ReturnVisitor(ast.NodeVisitor):
            def __init__(self) -> None:
                self.current_function: str | None = None
                self.returns: dict[str, list[ast.expr | None]] = {}

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                old_func = self.current_function
                self.current_function = node.name
                self.returns[node.name] = []
                self.generic_visit(node)
                self.current_function = old_func

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                self.visit_FunctionDef(node)  # type: ignore

            def visit_Return(self, node: ast.Return) -> None:
                if self.current_function:
                    self.returns[self.current_function].append(node.value)
                self.generic_visit(node)

        visitor = ReturnVisitor()
        visitor.visit(self._tree)

        for func_name, return_values in visitor.returns.items():
            inferred_type = self._infer_return_type(return_values)
            results[func_name] = {
                "return_count": len(return_values),
                "returns_none": any(v is None for v in return_values),
                "inferred_type": inferred_type,
            }

        return results

    def _infer_return_type(self, return_values: list[ast.expr | None]) -> str | None:
        """Attempt to infer return type from return statements."""
        if not return_values:
            return "None"

        types: set[str] = set()

        for value in return_values:
            if value is None:
                types.add("None")
            elif isinstance(value, ast.Constant):
                types.add(type(value.value).__name__)
            elif isinstance(value, ast.List):
                types.add("list")
            elif isinstance(value, ast.Dict):
                types.add("dict")
            elif isinstance(value, ast.Set):
                types.add("set")
            elif isinstance(value, ast.Tuple):
                types.add("tuple")
            elif isinstance(value, ast.Call):
                if isinstance(value.func, ast.Name):
                    types.add(value.func.id)
            elif isinstance(value, ast.Name):
                types.add("Any")  # Variable, type unknown

        if len(types) == 1:
            return types.pop()
        elif len(types) > 1:
            return " | ".join(sorted(types))
        return None

    def _find_unused_imports(self) -> list[str]:
        """Find imports that are never used in the module."""
        if self._tree is None:
            return []

        imported_names: set[str] = set()
        used_names: set[str] = set()

        # Collect imported names
        for node in ast.walk(self._tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name.split(".")[0]
                    imported_names.add(name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != "*":
                        name = alias.asname if alias.asname else alias.name
                        imported_names.add(name)

        # Collect used names (excluding import statements)
        class NameCollector(ast.NodeVisitor):
            def visit_Name(self, node: ast.Name) -> None:
                used_names.add(node.id)
                self.generic_visit(node)

            def visit_Attribute(self, node: ast.Attribute) -> None:
                # Get the root name of attribute access
                current = node
                while isinstance(current, ast.Attribute):
                    current = current.value  # type: ignore
                if isinstance(current, ast.Name):
                    used_names.add(current.id)
                self.generic_visit(node)

        collector = NameCollector()
        for node in self._tree.body:
            if not isinstance(node, ast.Import | ast.ImportFrom):
                collector.visit(node)

        return sorted(imported_names - used_names)

    def _analyze_name_bindings(self) -> dict[str, list[dict[str, Any]]]:
        """Analyze where names are bound (assigned) in the module."""
        if self._tree is None:
            return {}

        bindings: dict[str, list[dict[str, Any]]] = {}

        class BindingVisitor(ast.NodeVisitor):
            def __init__(self) -> None:
                self.scope_stack: list[str] = ["<module>"]

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                self.scope_stack.append(node.name)
                # Add function parameters as bindings
                for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
                    self._add_binding(arg.arg, node.lineno, "parameter")
                if node.args.vararg:
                    self._add_binding(node.args.vararg.arg, node.lineno, "parameter")
                if node.args.kwarg:
                    self._add_binding(node.args.kwarg.arg, node.lineno, "parameter")
                self.generic_visit(node)
                self.scope_stack.pop()

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                self.visit_FunctionDef(node)  # type: ignore

            def visit_ClassDef(self, node: ast.ClassDef) -> None:
                self.scope_stack.append(node.name)
                self.generic_visit(node)
                self.scope_stack.pop()

            def visit_Assign(self, node: ast.Assign) -> None:
                for target in node.targets:
                    self._collect_assign_targets(target, node.lineno)
                self.generic_visit(node)

            def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
                if isinstance(node.target, ast.Name):
                    self._add_binding(node.target.id, node.lineno, "annotated_assignment")
                self.generic_visit(node)

            def visit_For(self, node: ast.For) -> None:
                self._collect_assign_targets(node.target, node.lineno)
                self.generic_visit(node)

            def visit_With(self, node: ast.With) -> None:
                for item in node.items:
                    if item.optional_vars:
                        self._collect_assign_targets(item.optional_vars, node.lineno)
                self.generic_visit(node)

            def _collect_assign_targets(self, target: ast.expr, lineno: int) -> None:
                if isinstance(target, ast.Name):
                    self._add_binding(target.id, lineno, "assignment")
                elif isinstance(target, ast.Tuple | ast.List):
                    for elt in target.elts:
                        self._collect_assign_targets(elt, lineno)

            def _add_binding(self, name: str, lineno: int, kind: str) -> None:
                scope = ".".join(self.scope_stack)
                if name not in bindings:
                    bindings[name] = []
                bindings[name].append({
                    "scope": scope,
                    "line": lineno,
                    "kind": kind,
                })

        visitor = BindingVisitor()
        visitor.visit(self._tree)

        return bindings

    def _get_mro_info(self, class_name: str) -> list[str] | None:
        """Get method resolution order info for a class if determinable."""
        if self._tree is None:
            return None

        for node in ast.walk(self._tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return [ast.unparse(base) for base in node.bases]

        return None

    def get_all_names_in_scope(self, scope: str) -> set[str]:
        """Get all names visible in a given scope."""
        if self._tree is None:
            return set()

        names: set[str] = set()
        scope_parts = scope.split(".")

        class ScopeVisitor(ast.NodeVisitor):
            def __init__(self, target_scope: list[str]) -> None:
                self.target_scope = target_scope
                self.current_scope: list[str] = []
                self.found = False

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                self.current_scope.append(node.name)
                if self.current_scope == self.target_scope:
                    self.found = True
                    # Collect names in this function
                    for arg in node.args.args:
                        names.add(arg.arg)
                self.generic_visit(node)
                self.current_scope.pop()

            def visit_ClassDef(self, node: ast.ClassDef) -> None:
                self.current_scope.append(node.name)
                if self.current_scope == self.target_scope:
                    self.found = True
                self.generic_visit(node)
                self.current_scope.pop()

        visitor = ScopeVisitor(scope_parts[1:] if scope_parts[0] == "<module>" else scope_parts)
        visitor.visit(self._tree)

        # Always include module-level names
        names.update(self._extract_global_names())

        return names
