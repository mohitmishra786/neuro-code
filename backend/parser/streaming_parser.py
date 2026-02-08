"""
NeuroCode Streaming Project Parser.

Processes large codebases in chunks to prevent memory exhaustion.
Requires Python 3.11+.
"""

import asyncio
from collections import deque
from pathlib import Path
from typing import Iterator

from parser.project_parser import ProjectParser
from parser.models import PackageInfo, ModuleInfo, Relationship
from utils.logger import LoggerMixin
from utils.config import get_settings


class StreamingProjectParser(LoggerMixin):
    """
    Memory-efficient parser for large codebases.

    Processes files in configurable chunks to prevent memory exhaustion.
    Uses async processing for better throughput on large projects.
    """

    def __init__(self, root_path: Path, chunk_size: int = 100):
        """
        Initialize streaming parser.

        Args:
            root_path: Root directory of the Python project
            chunk_size: Number of files to process per chunk
        """
        self.root = root_path.resolve()
        self.chunk_size = chunk_size
        self._base_parser = ProjectParser(self.root)

        settings = get_settings()
        self._max_workers = settings.parser.max_workers

        # Streaming state
        self._total_files = 0
        self._processed_files = 0
        self._current_chunk: list[Path] = []

        # Results accumulated across chunks
        self._packages: list[PackageInfo] = []
        self._modules: list[ModuleInfo] = []
        self._relationships: list[Relationship] = []
        self._errors: list[str] = []

    async def _discover_files_async(self) -> list[Path]:
        """Discover files asynchronously using thread pool."""
        def discover():
            return self._base_parser._discover_files()
        return await asyncio.to_thread(discover)

    async def _parse_chunk_async(self, chunk_files: list[Path]) -> tuple[list[PackageInfo], list[ModuleInfo], list[Relationship], list[str]]:
        """Parse a single chunk asynchronously."""
        def parse():
            chunk_parser = ProjectParser(self.root)
            chunk_parser._discover_files = lambda files=chunk_files: files
            return chunk_parser.parse_project()

        packages, modules, relationships = await asyncio.to_thread(parse)
        return packages, modules, relationships, []

    async def parse_project_parallel(self) -> tuple[list[PackageInfo], list[ModuleInfo], list[Relationship], list[str]]:
        """
        Parse project with parallel file processing.

        Uses semaphore to limit concurrent chunks and thread pool for I/O.

        Returns:
            Tuple of (packages, modules, relationships, errors)
        """
        self.log.info("starting_parallel_parse", chunk_size=self.chunk_size, max_workers=self._max_workers)

        all_files = await self._discover_files_async()
        self._total_files = len(all_files)

        if not all_files:
            return [], [], [], []

        chunks = [
            all_files[i:i + self.chunk_size]
            for i in range(0, self._total_files, self.chunk_size)
        ]

        semaphore = asyncio.Semaphore(self._max_workers)

        async def process_chunk_with_semaphore(chunk_files: list[Path]) -> tuple[list[PackageInfo], list[ModuleInfo], list[Relationship], list[str]]:
            async with semaphore:
                return await self._parse_chunk_async(chunk_files)

        tasks = [process_chunk_with_semaphore(chunk) for chunk in chunks]

        async def gather_with_errors() -> list[tuple[list[PackageInfo], list[ModuleInfo], list[Relationship], list[str]]]:
            results = []
            for task in asyncio.as_completed(tasks):
                try:
                    result = await task
                    results.append(result)
                except Exception as e:
                    self._errors.append(str(e))
            return results

        all_results = await gather_with_errors()

        seen_ids = set()
        for packages, modules, relationships, _ in all_results:
            self._modules.extend(modules)
            self._relationships.extend(relationships)

            for pkg in packages:
                if pkg.id not in seen_ids:
                    seen_ids.add(pkg.id)
                    self._packages.append(pkg)

        self._processed_files = self._total_files

        self.log.info(
            "parallel_parse_complete",
            total_files=self._total_files,
            total_errors=len(self._errors),
        )

        return self._packages, self._modules, self._relationships, self._errors

    def parse_project_streaming(self) -> Iterator[tuple[list[PackageInfo], list[ModuleInfo], list[Relationship], list[str]]]:
        """
        Parse project in chunks, yielding results for each chunk.

        Yields:
            Tuple of (packages, modules, relationships, errors) for each chunk
        """
        all_files = self._base_parser._discover_files()
        self._total_files = len(all_files)

        self.log.info(
            "starting_streaming_parse",
            total_files=self._total_files,
            chunk_size=self.chunk_size,
        )

        for chunk_start in range(0, self._total_files, self.chunk_size):
            chunk_end = min(chunk_start + self.chunk_size, self._total_files)
            chunk_files = all_files[chunk_start:chunk_end]

            self.log.info(
                "processing_chunk",
                chunk_start=chunk_start,
                chunk_end=chunk_end,
                chunk_size=len(chunk_files),
            )

            try:
                chunk_parser = ProjectParser(self.root)
                chunk_parser._discover_files = lambda files=chunk_files: files

                packages, modules, relationships = chunk_parser.parse_project()

                self._packages.extend(packages)
                self._modules.extend(modules)
                self._relationships.extend(relationships)

                unique_packages = []
                seen_ids = set()
                for pkg in self._packages:
                    if pkg.id not in seen_ids:
                        seen_ids.add(pkg.id)
                        unique_packages.append(pkg)
                self._packages = unique_packages

                self._processed_files += len(chunk_files)

                yield packages, modules, relationships, []

                del chunk_parser

            except Exception as e:
                error_msg = f"Chunk {chunk_start}-{chunk_end}: {e}"
                self._errors.append(error_msg)
                self.log.error("chunk_parse_error", chunk_start=chunk_start, error=str(e))
                yield [], [], [], [error_msg]

        self.log.info(
            "streaming_parse_complete",
            total_files=self._total_files,
            processed_files=self._processed_files,
            total_errors=len(self._errors),
        )

    def get_final_results(self) -> tuple[list[PackageInfo], list[ModuleInfo], list[Relationship], list[str]]:
        """
        Get accumulated results from all chunks.

        Returns:
            Tuple of (packages, modules, relationships, errors)
        """
        return self._packages, self._modules, self._relationships, self._errors

    def get_progress(self) -> dict[str, float]:
        """Get current parsing progress."""
        if self._total_files == 0:
            return {"progress": 0.0, "processed": 0, "total": 0}
        return {
            "progress": self._processed_files / self._total_files,
            "processed": self._processed_files,
            "total": self._total_files,
        }
