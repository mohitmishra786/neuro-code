"""
Tests for Hash Calculator.

Requires Python 3.11+.
"""

from pathlib import Path

import pytest

from parser.tree_sitter_parser import TreeSitterParser
from merkle.hash_calculator import HashCalculator


class TestHashCalculator:
    """Test cases for HashCalculator."""

    @pytest.fixture
    def hasher(self) -> HashCalculator:
        """Create a hash calculator instance."""
        return HashCalculator()

    @pytest.fixture
    def parser(self) -> TreeSitterParser:
        """Create a parser instance."""
        return TreeSitterParser()

    def test_hash_module(self, hasher: HashCalculator, parser: TreeSitterParser, sample_python_code: str):
        """Test module hashing."""
        module = parser.parse_content(sample_python_code, Path("test.py"))
        hash1 = hasher.hash_module(module)

        assert hash1 is not None
        assert len(hash1) == 64  # SHA-256 hex length

        # Same content should produce same hash
        module2 = parser.parse_content(sample_python_code, Path("test.py"))
        hash2 = hasher.hash_module(module2)

        assert hash1 == hash2

    def test_hash_changes_with_content(self, hasher: HashCalculator, parser: TreeSitterParser):
        """Test that hash changes when content changes."""
        code1 = "def foo(): return 1"
        code2 = "def foo(): return 2"

        module1 = parser.parse_content(code1, Path("test.py"))
        module2 = parser.parse_content(code2, Path("test.py"))

        hash1 = hasher.hash_module(module1)
        hash2 = hasher.hash_module(module2)

        assert hash1 != hash2

    def test_hash_function(self, hasher: HashCalculator, parser: TreeSitterParser, sample_python_code: str):
        """Test function hashing."""
        module = parser.parse_content(sample_python_code, Path("test.py"))
        func = next(f for f in module.functions if f.name == "standalone_function")

        hash1 = hasher.hash_function(func)
        assert hash1 is not None
        assert len(hash1) == 64

    def test_hash_class(self, hasher: HashCalculator, parser: TreeSitterParser, sample_python_code: str):
        """Test class hashing."""
        module = parser.parse_content(sample_python_code, Path("test.py"))
        cls = next(c for c in module.classes if c.name == "BaseClass")

        hash1 = hasher.hash_class(cls)
        assert hash1 is not None
        assert len(hash1) == 64

    def test_hash_tree(self, hasher: HashCalculator, parser: TreeSitterParser, sample_python_code: str):
        """Test tree hashing."""
        module = parser.parse_content(sample_python_code, Path("test.py"))
        tree_hashes = hasher.hash_tree(module)

        assert len(tree_hashes) > 0
        assert "test" in tree_hashes  # Module qualified name
        assert "test.BaseClass" in tree_hashes
        assert "test.DerivedClass" in tree_hashes
        assert "test.standalone_function" in tree_hashes

    def test_compare_hashes(self, hasher: HashCalculator):
        """Test hash comparison."""
        old_hashes = {
            "module.a": "hash_a",
            "module.b": "hash_b_old",
            "module.c": "hash_c",
        }
        new_hashes = {
            "module.a": "hash_a",
            "module.b": "hash_b_new",
            "module.d": "hash_d",
        }

        added, removed, modified = hasher.compare_hashes(old_hashes, new_hashes)

        assert "module.d" in added
        assert "module.c" in removed
        assert "module.b" in modified
        assert "module.a" not in modified

    def test_hash_stability(self, hasher: HashCalculator, parser: TreeSitterParser, sample_python_code: str):
        """Test that hashes are stable across multiple calculations."""
        module = parser.parse_content(sample_python_code, Path("test.py"))

        hashes1 = hasher.hash_tree(module)
        hashes2 = hasher.hash_tree(module)

        assert hashes1 == hashes2

    def test_hash_without_docstrings(self, parser: TreeSitterParser):
        """Test hashing with docstrings excluded."""
        hasher_with = HashCalculator(include_docstrings=True)
        hasher_without = HashCalculator(include_docstrings=False)

        code = '"""Docstring."""\ndef foo(): pass'
        module = parser.parse_content(code, Path("test.py"))

        hash_with = hasher_with.hash_module(module)
        hash_without = hasher_without.hash_module(module)

        assert hash_with != hash_without
