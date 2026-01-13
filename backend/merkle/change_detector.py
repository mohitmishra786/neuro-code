"""
NeuroCode Change Detector.

Detects code changes using Merkle tree comparison.
Requires Python 3.11+.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from merkle.hash_calculator import HashCalculator
from parser.models import ModuleInfo
from parser.tree_sitter_parser import TreeSitterParser
from utils.logger import LoggerMixin


@dataclass
class ChangeSet:
    """Represents a set of detected changes."""

    added_nodes: set[str] = field(default_factory=set)
    removed_nodes: set[str] = field(default_factory=set)
    modified_nodes: set[str] = field(default_factory=set)
    affected_modules: set[str] = field(default_factory=set)

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return bool(self.added_nodes or self.removed_nodes or self.modified_nodes)

    @property
    def total_changes(self) -> int:
        """Get total number of changes."""
        return len(self.added_nodes) + len(self.removed_nodes) + len(self.modified_nodes)

    def merge(self, other: "ChangeSet") -> "ChangeSet":
        """Merge another changeset into this one."""
        return ChangeSet(
            added_nodes=self.added_nodes | other.added_nodes,
            removed_nodes=self.removed_nodes | other.removed_nodes,
            modified_nodes=self.modified_nodes | other.modified_nodes,
            affected_modules=self.affected_modules | other.affected_modules,
        )


class ChangeDetector(LoggerMixin):
    """
    Detects changes in code using Merkle tree comparison.

    Maintains a cache of hashes and provides efficient
    incremental change detection.
    """

    def __init__(self) -> None:
        """Initialize the change detector."""
        self._parser = TreeSitterParser()
        self._hasher = HashCalculator()
        # Cache: path -> {qualified_name -> hash}
        self._hash_cache: dict[Path, dict[str, str]] = {}
        # Cache: path -> ModuleInfo
        self._module_cache: dict[Path, ModuleInfo] = {}

    def detect_changes(self, file_path: Path) -> ChangeSet:
        """
        Detect changes in a single file.

        Args:
            file_path: Path to the changed file

        Returns:
            ChangeSet containing all detected changes
        """
        changes = ChangeSet()

        if not file_path.exists():
            # File was deleted
            if file_path in self._hash_cache:
                old_hashes = self._hash_cache.pop(file_path)
                changes.removed_nodes = set(old_hashes.keys())
                changes.affected_modules.add(str(file_path))
                self._module_cache.pop(file_path, None)
                self.log.info(
                    "file_deleted",
                    path=str(file_path),
                    removed_count=len(changes.removed_nodes),
                )
            return changes

        # Parse the file
        try:
            new_module = self._parser.parse_file(file_path)
        except Exception as e:
            self.log.error("parse_failed", path=str(file_path), error=str(e))
            return changes

        # Calculate new hashes
        new_hashes = self._hasher.hash_tree(new_module)

        # Get old hashes if available
        old_hashes = self._hash_cache.get(file_path, {})

        # Compare hashes
        added, removed, modified = self._hasher.compare_hashes(old_hashes, new_hashes)

        changes.added_nodes = added
        changes.removed_nodes = removed
        changes.modified_nodes = modified
        changes.affected_modules.add(str(file_path))

        # Update cache
        self._hash_cache[file_path] = new_hashes
        self._module_cache[file_path] = new_module

        if changes.has_changes:
            self.log.info(
                "changes_detected",
                path=str(file_path),
                added=len(added),
                removed=len(removed),
                modified=len(modified),
            )

        return changes

    def detect_changes_batch(self, file_paths: list[Path]) -> ChangeSet:
        """
        Detect changes in multiple files.

        Args:
            file_paths: List of paths to check

        Returns:
            Merged ChangeSet for all files
        """
        combined = ChangeSet()

        for path in file_paths:
            file_changes = self.detect_changes(path)
            combined = combined.merge(file_changes)

        return combined

    def initialize_from_modules(self, modules: list[ModuleInfo]) -> None:
        """
        Initialize the hash cache from pre-parsed modules.

        Args:
            modules: List of already-parsed ModuleInfo objects
        """
        for module in modules:
            hashes = self._hasher.hash_tree(module)
            self._hash_cache[module.path] = hashes
            self._module_cache[module.path] = module

        self.log.info(
            "cache_initialized",
            module_count=len(modules),
            total_hashes=sum(len(h) for h in self._hash_cache.values()),
        )

    def get_module(self, file_path: Path) -> ModuleInfo | None:
        """Get cached module info for a file."""
        return self._module_cache.get(file_path)

    def get_all_modules(self) -> list[ModuleInfo]:
        """Get all cached modules."""
        return list(self._module_cache.values())

    def get_hash(self, file_path: Path, qualified_name: str) -> str | None:
        """Get the hash for a specific node."""
        file_hashes = self._hash_cache.get(file_path)
        if file_hashes:
            return file_hashes.get(qualified_name)
        return None

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._hash_cache.clear()
        self._module_cache.clear()
        self.log.info("cache_cleared")

    def remove_file(self, file_path: Path) -> set[str]:
        """
        Remove a file from the cache and return removed node names.

        Args:
            file_path: Path to remove

        Returns:
            Set of qualified names that were removed
        """
        removed_hashes = self._hash_cache.pop(file_path, {})
        self._module_cache.pop(file_path, None)
        return set(removed_hashes.keys())

    def get_affected_by_change(
        self, changed_qualified_name: str
    ) -> set[str]:
        """
        Get nodes that might be affected by a change to a node.

        This includes:
        - Parent nodes (containers)
        - Nodes that reference the changed node

        Args:
            changed_qualified_name: Qualified name of changed node

        Returns:
            Set of potentially affected qualified names
        """
        affected: set[str] = set()

        # Add all parent paths
        parts = changed_qualified_name.split(".")
        for i in range(1, len(parts)):
            parent = ".".join(parts[:i])
            affected.add(parent)

        # Note: Full reference analysis requires graph queries
        # This method only handles structural (containment) dependencies

        return affected

    def propagate_hash_changes(
        self, changes: ChangeSet
    ) -> dict[str, str]:
        """
        Propagate hash changes up the tree.

        When a child node changes, parent hashes also need to be recalculated.

        Args:
            changes: The detected changes

        Returns:
            Dictionary of qualified_name -> new_hash for all affected nodes
        """
        updated_hashes: dict[str, str] = {}
        affected_paths: set[Path] = set()

        # Find all affected paths
        for file_path, hashes in self._hash_cache.items():
            for name in changes.modified_nodes | changes.added_nodes | changes.removed_nodes:
                if name in hashes or any(
                    name.startswith(existing + ".") for existing in hashes
                ):
                    affected_paths.add(file_path)
                    break

        # Recalculate hashes for affected modules
        for path in affected_paths:
            module = self._module_cache.get(path)
            if module:
                new_hashes = self._hasher.hash_tree(module)
                self._hash_cache[path] = new_hashes
                updated_hashes.update(new_hashes)

        return updated_hashes

    def get_cache_stats(self) -> dict[str, Any]:
        """Get statistics about the cache."""
        total_hashes = sum(len(h) for h in self._hash_cache.values())
        return {
            "cached_files": len(self._hash_cache),
            "cached_modules": len(self._module_cache),
            "total_hashes": total_hashes,
        }
