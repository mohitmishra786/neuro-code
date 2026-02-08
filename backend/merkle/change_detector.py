"""
NeuroCode Change Detector.

Detects changes in code using Merkle tree comparison.
Requires Python 3.11+.
"""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from parser.models import ModuleInfo
from parser.tree_sitter_parser import TreeSitterParser
from merkle.hash_calculator import HashCalculator
from utils.logger import LoggerMixin


@dataclass
class ChangeSet:
    """Represents detected changes in the codebase."""
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
    incremental change detection with improved cross-file propagation.
    Thread-safe with async support.
    """

    def __init__(self) -> None:
        """Initialize the change detector."""
        self._parser = TreeSitterParser()
        self._hasher = HashCalculator()
        self._hash_cache: dict[Path, dict[str, str]] = {}
        self._module_cache: dict[Path, ModuleInfo] = {}
        self._lock = asyncio.Lock()

    async def detect_changes(self, file_path: Path) -> ChangeSet:
        """
        Detect changes in a single file.

        Thread-safe method for detecting changes.

        Args:
            file_path: Path to the changed file

        Returns:
            ChangeSet containing all detected changes
        """
        async with self._lock:
            return self._detect_changes_sync(file_path)

    def _detect_changes_sync(self, file_path: Path) -> ChangeSet:
        """Internal synchronous change detection."""
        changes = ChangeSet()

        if not file_path.exists():
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

        try:
            new_module = self._parser.parse_file(file_path)
        except Exception as e:
            self.log.error("parse_failed", path=str(file_path), error=str(e))
            return changes

        new_hashes = self._hasher.hash_tree(new_module)
        old_hashes = self._hash_cache.get(file_path, {})

        added, removed, modified = self._hasher.compare_hashes(old_hashes, new_hashes)

        changes.added_nodes = added
        changes.removed_nodes = removed
        changes.modified_nodes = modified
        changes.affected_modules.add(str(file_path))

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

    async def detect_changes_batch(self, file_paths: list[Path]) -> ChangeSet:
        """
        Detect changes in multiple files.

        Args:
            file_paths: List of paths to check

        Returns:
            Merged ChangeSet for all files
        """
        combined = ChangeSet()

        for path in file_paths:
            file_changes = await self.detect_changes(path)
            combined = combined.merge(file_changes)

        return combined

    async def initialize_from_modules(self, modules: list[ModuleInfo]) -> None:
        """
        Initialize the hash cache from pre-parsed modules.

        Args:
            modules: List of already-parsed ModuleInfo objects
        """
        async with self._lock:
            for module in modules:
                hashes = self._hasher.hash_tree(module)
                self._hash_cache[module.path] = hashes
                self._module_cache[module.path] = module

            self.log.info(
                "cache_initialized",
                module_count=len(modules),
                total_hashes=sum(len(h) for h in self._hash_cache.values()),
            )

    async def get_module(self, file_path: Path) -> ModuleInfo | None:
        """Get cached module info for a file."""
        async with self._lock:
            return self._module_cache.get(file_path)

    async def get_all_modules(self) -> list[ModuleInfo]:
        """Get all cached modules."""
        async with self._lock:
            return list(self._module_cache.values())

    async def get_hash(self, file_path: Path, qualified_name: str) -> str | None:
        """Get the hash for a specific node."""
        async with self._lock:
            file_hashes = self._hash_cache.get(file_path)
            if file_hashes:
                return file_hashes.get(qualified_name)
            return None

    async def clear_cache(self) -> None:
        """Clear all cached data."""
        async with self._lock:
            self._hash_cache.clear()
            self._module_cache.clear()
            self.log.info("cache_cleared")

    async def remove_file(self, file_path: Path) -> set[str]:
        """
        Remove a file from the cache and return removed node names.

        Args:
            file_path: Path to remove

        Returns:
            Set of qualified names that were removed
        """
        async with self._lock:
            removed_hashes = self._hash_cache.pop(file_path, {})
            self._module_cache.pop(file_path, None)
            return set(removed_hashes.keys())

    async def propagate_hash_changes(
        self, changes: ChangeSet
    ) -> dict[str, str]:
        """
        Propagate hash changes up the tree and across file references.

        Thread-safe method for propagating changes.

        Args:
            changes: The detected changes

        Returns:
            Dictionary of qualified_name -> new_hash for all affected nodes
        """
        async with self._lock:
            return self._propagate_changes_sync(changes)

    def _propagate_changes_sync(self, changes: ChangeSet) -> dict[str, str]:
        """Internal synchronous change propagation."""
        updated_hashes: dict[str, str] = {}
        affected_paths: set[Path] = set()

        nodes_to_recalc = set(changes.modified_nodes | changes.added_nodes | changes.removed_nodes)

        for file_path, module in self._module_cache.items():
            module_needs_recalc = False
            file_hashes = self._hash_cache.get(file_path, {})

            for name in list(nodes_to_recalc):
                if name in file_hashes:
                    module_needs_recalc = True
                    parts = name.split(".")
                    for i in range(1, len(parts)):
                        parent = ".".join(parts[:i])
                        nodes_to_recalc.add(parent)
                elif any(name.startswith(h + ".") for h in file_hashes.keys()):
                    module_needs_recalc = True
                    break

            if module_needs_recalc:
                affected_paths.add(file_path)

        for path in affected_paths:
            module = self._module_cache.get(path)
            if module:
                old_hashes = self._hash_cache.get(path, {})
                new_hashes = self._hasher.hash_tree(module)
                self._hash_cache[path] = new_hashes

                for name, new_hash in new_hashes.items():
                    old_hash = old_hashes.get(name)
                    if old_hash != new_hash:
                        updated_hashes[name] = new_hash

        if updated_hashes:
            self.log.info(
                "hash_changes_propagated",
                total_nodes=len(updated_hashes),
                affected_files=len(affected_paths),
            )

        return updated_hashes

    async def get_cache_stats(self) -> dict[str, Any]:
        """Get statistics about the cache."""
        async with self._lock:
            total_hashes = sum(len(h) for h in self._hash_cache.values())
            return {
                "cached_files": len(self._hash_cache),
                "cached_modules": len(self._module_cache),
                "total_hashes": total_hashes,
            }
