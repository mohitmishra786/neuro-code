#!/usr/bin/env python3
"""
NeuroCode Benchmark Script.

Performance benchmarks for parsing and graph operations.
Requires Python 3.11+.

Usage:
    python scripts/benchmark.py /path/to/python/project
"""

import argparse
import asyncio
import statistics
import sys
import time
from pathlib import Path
from typing import Callable, TypeVar

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from parser.tree_sitter_parser import TreeSitterParser
from parser.relationship_extractor import RelationshipExtractor
from merkle.hash_calculator import HashCalculator
from graph_db.neo4j_client import Neo4jClient
from utils.logger import configure_logging, get_logger


configure_logging()
logger = get_logger("benchmark")

T = TypeVar("T")


def benchmark(name: str, func: Callable[[], T], iterations: int = 5) -> tuple[T, dict]:
    """
    Benchmark a function.

    Returns:
        Tuple of (result, stats)
    """
    times = []
    result = None

    for i in range(iterations):
        start = time.perf_counter()
        result = func()
        elapsed = time.perf_counter() - start
        times.append(elapsed * 1000)  # Convert to ms

    stats = {
        "name": name,
        "iterations": iterations,
        "min_ms": min(times),
        "max_ms": max(times),
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
    }

    return result, stats


async def benchmark_async(name: str, func: Callable, iterations: int = 5) -> tuple:
    """Async version of benchmark."""
    times = []
    result = None

    for i in range(iterations):
        start = time.perf_counter()
        result = await func()
        elapsed = time.perf_counter() - start
        times.append(elapsed * 1000)

    stats = {
        "name": name,
        "iterations": iterations,
        "min_ms": min(times),
        "max_ms": max(times),
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
    }

    return result, stats


def print_stats(stats: dict) -> None:
    """Print benchmark statistics."""
    print(f"\n  {stats['name']}:")
    print(f"    Mean:   {stats['mean_ms']:.2f}ms")
    print(f"    Median: {stats['median_ms']:.2f}ms")
    print(f"    Min:    {stats['min_ms']:.2f}ms")
    print(f"    Max:    {stats['max_ms']:.2f}ms")
    if stats["stdev_ms"] > 0:
        print(f"    StdDev: {stats['stdev_ms']:.2f}ms")


async def run_benchmarks(codebase_path: Path) -> None:
    """Run all benchmarks."""
    print(f"\n=== NeuroCode Benchmarks ===")
    print(f"Codebase: {codebase_path}")

    # Find Python files
    python_files = list(codebase_path.rglob("*.py"))
    python_files = [f for f in python_files if "__pycache__" not in str(f)]
    print(f"Python files: {len(python_files)}")

    if not python_files:
        print("No Python files found!")
        return

    parser = TreeSitterParser()
    hasher = HashCalculator()
    extractor = RelationshipExtractor()

    # Benchmark: Single file parsing
    sample_file = python_files[0]
    _, stats = benchmark(
        f"Parse single file ({sample_file.name})",
        lambda: parser.parse_file(sample_file),
    )
    print_stats(stats)

    # Benchmark: Parse all files
    def parse_all():
        modules = []
        for f in python_files[:100]:  # Limit for benchmark
            try:
                modules.append(parser.parse_file(f))
            except Exception:
                pass
        return modules

    modules, stats = benchmark("Parse 100 files", parse_all, iterations=3)
    print_stats(stats)
    files_per_sec = len(modules) / (stats["mean_ms"] / 1000)
    print(f"    Files/sec: {files_per_sec:.1f}")

    # Benchmark: Hash calculation
    if modules:
        sample_module = modules[0]
        _, stats = benchmark(
            "Hash single module",
            lambda: hasher.hash_tree(sample_module),
        )
        print_stats(stats)

        # Hash all modules
        _, stats = benchmark(
            "Hash all modules",
            lambda: [hasher.hash_tree(m) for m in modules],
            iterations=3,
        )
        print_stats(stats)

    # Benchmark: Relationship extraction
    if len(modules) >= 2:
        _, stats = benchmark(
            "Extract relationships",
            lambda: extractor.extract_relationships(modules),
            iterations=3,
        )
        print_stats(stats)
        rels = extractor.extract_relationships(modules)
        print(f"    Relationships: {len(rels)}")

    # Benchmark: Neo4j operations (if available)
    print("\n  Neo4j Benchmarks:")
    client = Neo4jClient()
    try:
        await client.connect()

        # Root nodes query
        _, stats = await benchmark_async(
            "Get root nodes",
            client.get_root_nodes,
        )
        print_stats(stats)

        # Search query
        async def search():
            return await client.search_nodes("test", limit=50)

        _, stats = await benchmark_async("Search nodes", search)
        print_stats(stats)

        await client.close()

    except Exception as e:
        print(f"    Skipped (not connected): {e}")

    print("\n=== Benchmark Complete ===\n")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run NeuroCode performance benchmarks"
    )
    parser.add_argument(
        "path",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Path to Python codebase to benchmark",
    )

    args = parser.parse_args()

    if not args.path.exists():
        print(f"Error: Path does not exist: {args.path}")
        sys.exit(1)

    try:
        asyncio.run(run_benchmarks(args.path))
    except KeyboardInterrupt:
        print("\nCancelled by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
