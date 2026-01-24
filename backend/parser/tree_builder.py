"""
Tree Builder for Hierarchical Code Visualization.

Converts flat parse results into a recursive tree structure
suitable for hierarchical graph visualization (e.g., React Flow).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from parser.models import ParseResult, ModuleInfo, ClassInfo, FunctionInfo, VariableInfo

class TreeBuilder:
    """Builds a hierarchical tree from flat parse results."""

    def __init__(self, parse_result: ParseResult, root_path: str):
        self.result = parse_result
        self.root_path = Path(root_path)
        self.tree: Dict[str, Any] = {
            "id": "root",
            "type": "root",
            "label": "Project Root",
            "children": []
        }
        # hierarchy: package_path -> node_dict
        self._package_map: Dict[str, Dict[str, Any]] = {}

    def build(self) -> Dict[str, Any]:
        """Execute the tree building process."""
        for module in self.result.modules:
            self._process_module(module)
        
        return self.tree

    def _get_package_path(self, module_path: Path) -> str:
        """Derive package dotted path from file path relative to root."""
        try:
            rel_path = module_path.relative_to(self.root_path)
            # Remove filename to get directory path
            parent_parts = rel_path.parent.parts
            return ".".join(parent_parts)
        except ValueError:
            return ""

    def _get_or_create_package(self, package_path: str) -> Dict[str, Any]:
        """
        Recursively create package nodes.
        """
        if not package_path:
            return self.tree

        if package_path in self._package_map:
            return self._package_map[package_path]

        parts = package_path.split('.')
        current_path = ""
        parent_node = self.tree

        for part in parts:
            prev_path = current_path
            current_path = f"{current_path}.{part}" if current_path else part
            
            if current_path not in self._package_map:
                new_package = {
                    "id": f"pkg::{current_path}",
                    "type": "package",
                    "label": part,
                    "data": {
                        "qualified_name": current_path,
                        "level": "package"
                    },
                    "children": []
                }
                self._package_map[current_path] = new_package
                # Add to parent's children
                parent_node["children"].append(new_package)
            
            parent_node = self._package_map[current_path]

        return self._package_map[package_path]

    def _process_module(self, module: ModuleInfo):
        """Convert a module and its contents into nodes."""
        package_path = self._get_package_path(module.path)
        parent_package = self._get_or_create_package(package_path)
        
        module_node = {
            "id": module.id,
            "type": "module",
            "label": module.name,
            "data": {
                "path": str(module.path),
                "lines": module.lines_of_code,
                "docstring": module.docstring,
                "level": "module"
            },
            "children": []
        }

        # Add classes
        for cls in module.classes:
            module_node["children"].append(self._process_class(cls))

        # Add functions
        for func in module.functions:
            module_node["children"].append(self._process_function(func))
        
        # Add global variables (optional, might clutter)
        for var in module.variables:
             module_node["children"].append(self._process_variable(var))

        parent_package["children"].append(module_node)

    def _process_class(self, cls: ClassInfo) -> Dict[str, Any]:
        """Convert class info to node."""
        class_node = {
            "id": cls.id,
            "type": "class",
            "label": cls.name,
            "data": {
                "docstring": cls.docstring,
                "bases": cls.bases,
                "level": "class"
            },
            "children": []
        }

        for method in cls.methods:
            class_node["children"].append(self._process_function(method))
            
        for var in cls.class_variables:
            class_node["children"].append(self._process_variable(var))

        return class_node

    def _process_function(self, func: FunctionInfo) -> Dict[str, Any]:
        """Convert function info to node."""
        # Functions are typically leaves, but could contain inner functions/variables
        return {
            "id": func.id,
            "type": "function",
            "label": func.name,
            "data": {
                "signature": func.signature,
                "complexity": func.complexity,
                "is_async": func.is_async,
                "level": "function"
            },
            # Could add local variables here if needed
            "children": [] 
        }

    def _process_variable(self, var: VariableInfo) -> Dict[str, Any]:
        """Convert variable info to node."""
        return {
            "id": var.id,
            "type": "variable",
            "label": var.name,
             "data": {
                "type_hint": var.type_hint,
                "level": "variable"
            },
            "children": []
        }
