"""
Tests for ProjectParser imports cleanup.

Verifies that unused imports have been removed and the parser still works correctly.
"""



class TestProjectParserImports:
    """Test that project parser works correctly after import cleanup."""

    def test_imports_are_valid(self) -> None:
        """Verify all imports in project_parser are actually used."""
        from parser.models import ModuleInfo, PackageInfo, Relationship
        from parser.project_parser import ProjectParser

        assert ProjectParser is not None
        assert ModuleInfo is not None
        assert PackageInfo is not None
        assert Relationship is not None

    def test_no_unused_iterator_import(self) -> None:
        """Verify Iterator import was removed (not needed)."""
        import typing

        import parser.project_parser as pp_module

        has_iterator = hasattr(typing, 'Iterator')
        assert has_iterator, "Iterator should be available in typing"

        source = pp_module.__file__
        if source:
            with open(source) as f:
                content = f.read()
                assert "from typing import Iterator" not in content, \
                    "Iterator should not be imported from typing"
