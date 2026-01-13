"""
NeuroCode Hash Calculator.

SHA-256 based hash computation for Merkle tree nodes.
Requires Python 3.11+.
"""

import hashlib
import json
from typing import Any

from parser.models import (
    ClassInfo,
    FunctionInfo,
    ModuleInfo,
    VariableInfo,
    ImportInfo,
)
from utils.logger import LoggerMixin


class HashCalculator(LoggerMixin):
    """
    Calculates content-based hashes for code elements.

    Uses SHA-256 for cryptographic security and collision resistance.
    Hash components are carefully chosen to capture semantic changes
    while ignoring formatting/whitespace changes.
    """

    def __init__(self, include_docstrings: bool = True) -> None:
        """
        Initialize the hash calculator.

        Args:
            include_docstrings: Whether to include docstrings in hash calculation
        """
        self._include_docstrings = include_docstrings

    def hash_module(self, module: ModuleInfo) -> str:
        """
        Calculate hash for a module.

        Components:
        - File path (for identity)
        - Sorted import hashes
        - Sorted class hashes
        - Sorted function hashes
        - Sorted variable hashes

        Args:
            module: ModuleInfo to hash

        Returns:
            SHA-256 hash as hex string
        """
        components: list[str] = [
            str(module.path),
        ]

        if self._include_docstrings and module.docstring:
            components.append(module.docstring)

        # Add sorted import hashes
        import_hashes = sorted(self.hash_import(imp) for imp in module.imports)
        components.extend(import_hashes)

        # Add sorted class hashes
        class_hashes = sorted(self.hash_class(cls) for cls in module.classes)
        components.extend(class_hashes)

        # Add sorted function hashes
        function_hashes = sorted(self.hash_function(func) for func in module.functions)
        components.extend(function_hashes)

        # Add sorted variable hashes
        variable_hashes = sorted(self.hash_variable(var) for var in module.variables)
        components.extend(variable_hashes)

        return self._compute_hash(components)

    def hash_class(self, cls: ClassInfo) -> str:
        """
        Calculate hash for a class.

        Components:
        - Class name
        - Sorted base class names
        - Decorator names in order
        - Sorted method hashes
        - Sorted class variable hashes
        - Sorted instance variable hashes

        Args:
            cls: ClassInfo to hash

        Returns:
            SHA-256 hash as hex string
        """
        components: list[str] = [
            cls.name,
        ]

        # Add sorted base classes
        components.extend(sorted(cls.bases))

        # Add decorators in order (order matters for behavior)
        for decorator in cls.decorators:
            components.append(decorator.qualified_name)

        if self._include_docstrings and cls.docstring:
            components.append(cls.docstring)

        # Add sorted method hashes
        method_hashes = sorted(self.hash_function(method) for method in cls.methods)
        components.extend(method_hashes)

        # Add sorted class variable hashes
        class_var_hashes = sorted(
            self.hash_variable(var) for var in cls.class_variables
        )
        components.extend(class_var_hashes)

        # Add sorted instance variable hashes
        instance_var_hashes = sorted(
            self.hash_variable(var) for var in cls.instance_variables
        )
        components.extend(instance_var_hashes)

        # Add nested class hashes
        nested_hashes = sorted(self.hash_class(nested) for nested in cls.nested_classes)
        components.extend(nested_hashes)

        return self._compute_hash(components)

    def hash_function(self, func: FunctionInfo) -> str:
        """
        Calculate hash for a function.

        Components:
        - Function name
        - Parameter signature (name, type, default)
        - Return type
        - Decorator names in order
        - Async/generator status
        - Sorted called function names
        - Sorted local variable hashes

        Args:
            func: FunctionInfo to hash

        Returns:
            SHA-256 hash as hex string
        """
        components: list[str] = [
            func.name,
        ]

        # Add parameter signature
        for param in func.parameters:
            param_str = param.name
            if param.type_hint:
                param_str += f":{param.type_hint}"
            if param.default_value:
                param_str += f"={param.default_value}"
            if param.is_args:
                param_str = f"*{param_str}"
            if param.is_kwargs:
                param_str = f"**{param_str}"
            components.append(param_str)

        # Add return type
        if func.return_type:
            components.append(f"->{func.return_type}")

        # Add decorators in order
        for decorator in func.decorators:
            components.append(decorator.qualified_name)

        # Add flags
        if func.is_async:
            components.append("async")
        if func.is_generator:
            components.append("generator")

        if self._include_docstrings and func.docstring:
            components.append(func.docstring)

        # Add sorted called functions
        components.extend(sorted(func.calls))

        # Add sorted local variable hashes
        var_hashes = sorted(self.hash_variable(var) for var in func.variables)
        components.extend(var_hashes)

        # Add body hash if available
        if func.body_hash:
            components.append(func.body_hash)

        return self._compute_hash(components)

    def hash_variable(self, var: VariableInfo) -> str:
        """
        Calculate hash for a variable.

        Components:
        - Variable name
        - Type hint
        - Initial value (if literal)

        Args:
            var: VariableInfo to hash

        Returns:
            SHA-256 hash as hex string
        """
        components: list[str] = [var.name]

        if var.type_hint:
            components.append(var.type_hint)

        if var.initial_value:
            components.append(var.initial_value)

        return self._compute_hash(components)

    def hash_import(self, imp: ImportInfo) -> str:
        """
        Calculate hash for an import statement.

        Components:
        - Module name
        - Sorted imported names
        - Relative level (for relative imports)

        Args:
            imp: ImportInfo to hash

        Returns:
            SHA-256 hash as hex string
        """
        components: list[str] = [imp.module_name]

        if imp.is_relative:
            components.append(f"relative:{imp.relative_level}")

        components.extend(sorted(imp.imported_names))

        # Add aliases
        for name, alias in sorted(imp.aliases.items()):
            components.append(f"{name}={alias}")

        return self._compute_hash(components)

    def _compute_hash(self, components: list[str]) -> str:
        """
        Compute SHA-256 hash of components.

        Args:
            components: List of strings to hash

        Returns:
            SHA-256 hash as hex string
        """
        # Join with null separator to avoid collisions
        content = "\x00".join(str(c) for c in components if c)
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def hash_tree(self, module: ModuleInfo) -> dict[str, str]:
        """
        Calculate hashes for entire module tree.

        Returns a dictionary mapping qualified names to hashes
        for all nodes in the module.

        Args:
            module: ModuleInfo to hash

        Returns:
            Dictionary of qualified_name -> hash
        """
        hashes: dict[str, str] = {}

        # Hash all classes and their contents
        for cls in module.classes:
            self._hash_class_recursive(cls, hashes)

        # Hash all top-level functions
        for func in module.functions:
            func_hash = self.hash_function(func)
            hashes[func.qualified_name] = func_hash

        # Hash all top-level variables
        for var in module.variables:
            var_hash = self.hash_variable(var)
            qualified_name = f"{module.qualified_name}.{var.name}"
            hashes[qualified_name] = var_hash

        # Hash imports
        for i, imp in enumerate(module.imports):
            imp_hash = self.hash_import(imp)
            hashes[f"{module.qualified_name}.__import_{i}__"] = imp_hash

        # Hash the module itself (depends on all children)
        module_hash = self.hash_module(module)
        hashes[module.qualified_name] = module_hash
        module.hash = module_hash

        return hashes

    def _hash_class_recursive(
        self, cls: ClassInfo, hashes: dict[str, str]
    ) -> str:
        """Recursively hash a class and all its contents."""
        # Hash all methods
        for method in cls.methods:
            method_hash = self.hash_function(method)
            hashes[method.qualified_name] = method_hash

        # Hash all class variables
        for var in cls.all_variables:
            var_hash = self.hash_variable(var)
            qualified_name = f"{cls.qualified_name}.{var.name}"
            hashes[qualified_name] = var_hash

        # Hash nested classes
        for nested in cls.nested_classes:
            self._hash_class_recursive(nested, hashes)

        # Hash the class itself
        class_hash = self.hash_class(cls)
        hashes[cls.qualified_name] = class_hash

        return class_hash

    def compare_hashes(
        self, old_hashes: dict[str, str], new_hashes: dict[str, str]
    ) -> tuple[set[str], set[str], set[str]]:
        """
        Compare two hash dictionaries to find changes.

        Args:
            old_hashes: Previous hash dictionary
            new_hashes: Current hash dictionary

        Returns:
            Tuple of (added, removed, modified) qualified names
        """
        old_keys = set(old_hashes.keys())
        new_keys = set(new_hashes.keys())

        added = new_keys - old_keys
        removed = old_keys - new_keys
        common = old_keys & new_keys

        modified = {
            key for key in common
            if old_hashes[key] != new_hashes[key]
        }

        return added, removed, modified
