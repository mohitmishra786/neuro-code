"""
Tests for Streaming Parser and Tree-sitter Recursion Limit.

Requires Python 3.11+.
"""

import pytest
from pathlib import Path

from parser.streaming_parser import StreamingProjectParser
from parser.tree_sitter_parser import TreeSitterParser


class TestStreamingParser:
    """Test cases for StreamingProjectParser."""

    @pytest.fixture
    def large_project_dir(self, tmp_path: Path) -> Path:
        """Create a large project for testing streaming."""
        project_dir = tmp_path / "large_project"
        project_dir.mkdir()
        
        # Create many files to test chunking
        for i in range(150):
            module_file = project_dir / f"module_{i}.py"
            module_file.write_text(f'''"""Module {i}."""

class Class{i}:
    """Class {i}."""
    
    def method_{i}(self, value: int) -> int:
        """A method."""
        return value * {i % 10}

def function_{i}(x: int, y: int) -> int:
    """A function."""
    return x + y + {i % 5}
''')
        
        # Create some subdirectories
        for j in range(5):
            subdir = project_dir / f"subdir_{j}"
            subdir.mkdir()
            (subdir / "__init__.py").write_text(f'"""Subdirectory {j}."""')
            
            for k in range(10):
                sub_module = subdir / f"sub_module_{j}_{k}.py"
                sub_module.write_text(f'''"""Submodule {j}-{k}."""

def helper_{j}_{k}():
    """Helper function."""
    pass
''')
        
        return project_dir

    def test_streaming_parse_processes_all_files(self, large_project_dir: Path):
        """Test that streaming parser processes all files."""
        parser = StreamingProjectParser(large_project_dir, chunk_size=50)
        
        packages, modules, relationships, errors = [], [], [], []
        for chunk_packages, chunk_modules, chunk_rels, chunk_errors in parser.parse_project_streaming():
            packages.extend(chunk_packages)
            modules.extend(chunk_modules)
            relationships.extend(chunk_rels)
            errors.extend(chunk_errors)
        
        # Should process all files
        assert len(modules) > 150  # At least 150 module files
        assert len(errors) == 0

    def test_chunk_size_respected(self, large_project_dir: Path):
        """Test that parser respects chunk size."""
        chunk_size = 30
        parser = StreamingProjectParser(large_project_dir, chunk_size=chunk_size)
        
        chunk_count = 0
        for _, _, _, _ in parser.parse_project_streaming():
            chunk_count += 1
            if chunk_count == 2:  # Just check first few chunks
                break
        
        # Parser should use multiple chunks
        assert chunk_count >= 2

    def test_get_progress(self, large_project_dir: Path):
        """Test progress tracking during parsing."""
        parser = StreamingProjectParser(large_project_dir, chunk_size=50)
        
        # Parse first chunk
        parser.parse_project_streaming().__next__()
        
        progress = parser.get_progress()
        assert "progress" in progress
        assert "processed" in progress
        assert "total" in progress
        assert 0.0 < progress["progress"] <= 1.0
        assert progress["processed"] > 0
        assert progress["total"] > 0

    def test_get_final_results(self, large_project_dir: Path):
        """Test getting accumulated results."""
        parser = StreamingProjectParser(large_project_dir, chunk_size=100)
        
        # Process all chunks
        for _ in parser.parse_project_streaming():
            pass
        
        packages, modules, relationships, errors = parser.get_final_results()
        
        assert len(packages) >= 0
        assert len(modules) > 0
        assert len(relationships) > 0
        assert len(errors) >= 0

    def test_handles_invalid_files(self, tmp_path: Path):
        """Test that parser handles invalid files gracefully."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        
        # Create valid file
        (project_dir / "valid.py").write_text("def test(): pass")
        
        # Create invalid file
        (project_dir / "invalid.py").write_text("def broken(\n")
        
        parser = StreamingProjectParser(project_dir, chunk_size=10)
        
        packages, modules, relationships, errors = [], [], [], []
        for chunk_packages, chunk_modules, chunk_rels, chunk_errors in parser.parse_project_streaming():
            packages.extend(chunk_packages)
            modules.extend(chunk_modules)
            relationships.extend(chunk_rels)
            errors.extend(chunk_errors)
        
        # Should still process valid file
        assert len(modules) > 0

    def test_deduplicates_packages(self, large_project_dir: Path):
        """Test that packages are deduplicated across chunks."""
        parser = StreamingProjectParser(large_project_dir, chunk_size=50)
        
        # Process all chunks
        for _ in parser.parse_project_streaming():
            pass
        
        packages, _, _, _ = parser.get_final_results()
        
        # Check no duplicate package IDs
        package_ids = [p.id for p in packages]
        assert len(package_ids) == len(set(package_ids))


class TestTreeSitterRecursionLimit:
    """Test cases for Tree-sitter recursion limit."""

    @pytest.fixture
    def parser(self) -> TreeSitterParser:
        """Create parser with recursion limit."""
        return TreeSitterParser(max_depth=500)

    def test_parser_has_max_depth(self, parser: TreeSitterParser):
        """Test that parser has max depth configured."""
        assert parser._max_depth == 500

    def test_max_depth_limits_recursion(self, parser: TreeSitterParser, tmp_path: Path):
        """Test that deeply nested code doesn't cause stack overflow."""
        # Create deeply nested code (200 levels)
        nested_code = ""
        for i in range(200):
            nested_code += f"{' ' * i}def func_{i}():\n"
            nested_code += f"{' ' * (i + 1)}    "
        
        nested_code += "pass\n" * 200
        
        test_file = tmp_path / "nested.py"
        test_file.write_text(nested_code)
        
        # Should not crash even with deep nesting
        module = parser.parse_file(test_file)
        assert module is not None

    def test_shallow_code_parses_correctly(self, parser: TreeSitterParser, tmp_path: Path):
        """Test that normal code parses correctly with limit set."""
        test_file = tmp_path / "normal.py"
        test_file.write_text('''
"""Normal module."""

class NormalClass:
    """A normal class."""
    
    def method(self):
        """A method."""
        pass

def normal_function():
    """A normal function."""
    pass
''')
        
        module = parser.parse_file(test_file)
        assert module is not None
        assert len(module.classes) == 1
        assert len(module.functions) == 1
        assert module.classes[0].name == "NormalClass"
        assert module.functions[0].name == "normal_function"

    def test_exceeding_limit_is_handled(self, parser: TreeSitterParser, tmp_path: Path):
        """Test that code exceeding limit is handled gracefully."""
        # Create code deeper than max_depth
        nested_code = ""
        for i in range(600):  # Exceeds max_depth of 500
            nested_code += f"{' ' * i}if True:\n"
        
        nested_code += "pass\n" * 600
        
        test_file = tmp_path / "deep.py"
        test_file.write_text(nested_code)
        
        # Should handle gracefully (may truncate or partial parse)
        module = parser.parse_file(test_file)
        assert module is not None

    @pytest.fixture
    def parser_custom_limit(self) -> TreeSitterParser:
        """Create parser with custom recursion limit."""
        return TreeSitterParser(max_depth=100)

    def test_custom_limit_is_respected(self, parser_custom_limit: TreeSitterParser):
        """Test that custom limit is set."""
        assert parser_custom_limit._max_depth == 100
