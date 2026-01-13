"""
Tests for Tree-sitter Parser.

Requires Python 3.11+.
"""

from pathlib import Path

import pytest

from parser.tree_sitter_parser import TreeSitterParser
from parser.models import NodeType


class TestTreeSitterParser:
    """Test cases for TreeSitterParser."""

    @pytest.fixture
    def parser(self) -> TreeSitterParser:
        """Create a parser instance."""
        return TreeSitterParser()

    def test_parse_file(self, parser: TreeSitterParser, temp_python_file: Path):
        """Test parsing a Python file."""
        module = parser.parse_file(temp_python_file)

        assert module is not None
        assert module.name == "sample"
        assert module.path == temp_python_file
        assert module.docstring == "Sample module docstring."

    def test_parse_content(self, parser: TreeSitterParser, sample_python_code: str):
        """Test parsing Python content directly."""
        module = parser.parse_content(sample_python_code, Path("test.py"))

        assert module is not None
        assert module.name == "test"

    def test_extract_imports(self, parser: TreeSitterParser, sample_python_code: str):
        """Test import extraction."""
        module = parser.parse_content(sample_python_code, Path("test.py"))

        assert len(module.imports) == 2
        import_names = [imp.module_name for imp in module.imports]
        assert "os" in import_names
        assert "typing" in import_names

    def test_extract_classes(self, parser: TreeSitterParser, sample_python_code: str):
        """Test class extraction."""
        module = parser.parse_content(sample_python_code, Path("test.py"))

        assert len(module.classes) == 2
        class_names = [cls.name for cls in module.classes]
        assert "BaseClass" in class_names
        assert "DerivedClass" in class_names

    def test_extract_class_methods(self, parser: TreeSitterParser, sample_python_code: str):
        """Test method extraction from classes."""
        module = parser.parse_content(sample_python_code, Path("test.py"))

        derived_class = next(c for c in module.classes if c.name == "DerivedClass")
        method_names = [m.name for m in derived_class.methods]

        assert "__init__" in method_names
        assert "async_method" in method_names
        assert "display_name" in method_names

    def test_extract_async_methods(self, parser: TreeSitterParser, sample_python_code: str):
        """Test async method detection."""
        module = parser.parse_content(sample_python_code, Path("test.py"))

        derived_class = next(c for c in module.classes if c.name == "DerivedClass")
        async_method = next(m for m in derived_class.methods if m.name == "async_method")

        assert async_method.is_async is True

    def test_extract_properties(self, parser: TreeSitterParser, sample_python_code: str):
        """Test property detection."""
        module = parser.parse_content(sample_python_code, Path("test.py"))

        derived_class = next(c for c in module.classes if c.name == "DerivedClass")
        display_name = next(m for m in derived_class.methods if m.name == "display_name")

        assert display_name.is_property is True

    def test_extract_functions(self, parser: TreeSitterParser, sample_python_code: str):
        """Test function extraction."""
        module = parser.parse_content(sample_python_code, Path("test.py"))

        func_names = [f.name for f in module.functions]
        assert "standalone_function" in func_names
        assert "async_generator" in func_names

    def test_extract_function_parameters(self, parser: TreeSitterParser, sample_python_code: str):
        """Test function parameter extraction."""
        module = parser.parse_content(sample_python_code, Path("test.py"))

        standalone_func = next(f for f in module.functions if f.name == "standalone_function")
        param_names = [p.name for p in standalone_func.parameters]

        assert "x" in param_names
        assert "y" in param_names

        y_param = next(p for p in standalone_func.parameters if p.name == "y")
        assert y_param.default_value == "10"

    def test_extract_module_variables(self, parser: TreeSitterParser, sample_python_code: str):
        """Test module-level variable extraction."""
        module = parser.parse_content(sample_python_code, Path("test.py"))

        var_names = [v.name for v in module.variables]
        assert "CONSTANT_VALUE" in var_names
        assert "_PRIVATE_CONSTANT" in var_names

    def test_extract_class_inheritance(self, parser: TreeSitterParser, sample_python_code: str):
        """Test class inheritance extraction."""
        module = parser.parse_content(sample_python_code, Path("test.py"))

        derived_class = next(c for c in module.classes if c.name == "DerivedClass")
        assert "BaseClass" in derived_class.bases

    def test_extract_docstrings(self, parser: TreeSitterParser, sample_python_code: str):
        """Test docstring extraction."""
        module = parser.parse_content(sample_python_code, Path("test.py"))

        assert module.docstring == "Sample module docstring."

        base_class = next(c for c in module.classes if c.name == "BaseClass")
        assert base_class.docstring == "A base class."

        standalone_func = next(f for f in module.functions if f.name == "standalone_function")
        assert standalone_func.docstring == "A standalone function."

    def test_source_location(self, parser: TreeSitterParser, sample_python_code: str):
        """Test source location tracking."""
        module = parser.parse_content(sample_python_code, Path("test.py"))

        base_class = next(c for c in module.classes if c.name == "BaseClass")
        assert base_class.location is not None
        assert base_class.location.line > 0

    def test_qualified_names(self, parser: TreeSitterParser, sample_python_code: str):
        """Test qualified name generation."""
        module = parser.parse_content(sample_python_code, Path("test.py"))

        assert module.qualified_name == "test"

        base_class = next(c for c in module.classes if c.name == "BaseClass")
        assert base_class.qualified_name == "test.BaseClass"

        method = next(m for m in base_class.methods if m.name == "method")
        assert method.qualified_name == "test.BaseClass.method"

    def test_empty_file(self, parser: TreeSitterParser, tmp_path: Path):
        """Test parsing an empty file."""
        empty_file = tmp_path / "empty.py"
        empty_file.write_text("")

        module = parser.parse_file(empty_file)

        assert module is not None
        assert len(module.classes) == 0
        assert len(module.functions) == 0

    def test_syntax_error_handling(self, parser: TreeSitterParser, tmp_path: Path):
        """Test handling of syntax errors."""
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("def broken(\n")

        # Should not raise, but may have incomplete parsing
        module = parser.parse_file(bad_file)
        assert module is not None
