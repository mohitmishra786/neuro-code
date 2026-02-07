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
        
        # Streaming state
        self._total_files = 0
        self._processed_files = 0
        self._current_chunk: list[Path] = []
        
        # Results accumulated across chunks
        self._packages: list[PackageInfo] = []
        self._modules: list[ModuleInfo] = []
        self._relationships: list[Relationship] = []
        self._errors: list[str] = []

    def parse_project_streaming(self) -> Iterator[tuple[list[PackageInfo], list[ModuleInfo], list[Relationship], list[str]]]:
        """
        Parse project in chunks, yielding results for each chunk.

        Yields:
            Tuple of (packages, modules, relationships, errors) for each chunk
        """
        # Discover all files first
        all_files = self._base_parser._discover_files()
        self._total_files = len(all_files)
        
        self.log.info(
            "starting_streaming_parse",
            total_files=self._total_files,
            chunk_size=self.chunk_size,
        )

        # Process files in chunks
        for chunk_start in range(0, self._total_files, self.chunk_size):
            chunk_end = min(chunk_start + self.chunk_size, self._total_files)
            chunk_files = all_files[chunk_start:chunk_end]
            
            self.log.info(
                "processing_chunk",
                chunk_start=chunk_start,
                chunk_end=chunk_end,
                chunk_size=len(chunk_files),
            )

            # Process this chunk
            try:
                # Create a temporary parser for this chunk
                chunk_parser = ProjectParser(self.root)
                
                # Override discovered files to process only this chunk
                chunk_files_set = set(chunk_files)
                original_discover = chunk_parser._discover_files
                chunk_parser._discover_files = lambda: chunk_files
                
                # Parse the chunk
                packages, modules, relationships = chunk_parser.parse_project()
                
                # Accumulate results
                self._packages.extend(packages)
                self._modules.extend(modules)
                self._relationships.extend(relationships)
                
                # Filter out duplicate packages (they might appear in multiple chunks)
                unique_packages = []
                seen_ids = set()
                for pkg in self._packages:
                    if pkg.id not in seen_ids:
                        seen_ids.add(pkg.id)
                        unique_packages.append(pkg)
                self._packages = unique_packages
                
                self._processed_files += len(chunk_files)
                
                # Yield results for this chunk
                yield packages, modules, relationships, []
                
                # Clear chunk parser to free memory
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

    async def parse_project_async(self) -> tuple[list[PackageInfo], list[ModuleInfo], list[Relationship], list[str]]:
        """
        Parse project asynchronously with semaphored concurrency control.

        Processes chunks concurrently but with a semaphore to limit memory usage.

        Returns:
            Tuple of (packages, modules, relationships, errors)
        """
        settings = get_settings()
        max_concurrent_chunks = getattr(settings.parser, 'max_workers', 4)
        semaphore = asyncio.Semaphore(max_concurrent_chunks)

        async def process_chunk(chunk_files: list[Path]) -> tuple[list[PackageInfo], list[ModuleInfo], list[Relationship], list[str]]:
            async with semaphore:
                def _parse():
                    chunk_parser = ProjectParser(self.root)
                    chunk_parser._discover_files = lambda: chunk_files
                    return chunk_parser.parse_project()
                
                return await asyncio.to_thread(_parse)

        # Discover all files
        all_files = self._base_parser._discover_files()
        self._total_files = len(all_files)

        # Split into chunks
        chunks = [
            all_files[i:i + self.chunk_size]
            for i in range(0, self._total_files, self.chunk_size)
        ]

        self.log.info(
            "starting_async_parse",
            total_files=self._total_files,
            chunks=len(chunks),
            max_concurrent=max_concurrent_chunks,
        )

        # Process chunks concurrently
        tasks = [process_chunk(chunk) for chunk in chunks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Accumulate results
        seen_ids = set()
        for result in results:
            if isinstance(result, Exception):
                self._errors.append(str(result))
                continue

            packages, modules, relationships = result
            self._modules.extend(modules)
            self._relationships.extend(relationships)
            
            # Deduplicate packages
            for pkg in packages:
                if pkg.id not in seen_ids:
                    seen_ids.add(pkg.id)
                    self._packages.append(pkg)

        self.log.info(
            "async_parse_complete",
            total_files=self._total_files,
            total_errors=len(self._errors),
        )

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
