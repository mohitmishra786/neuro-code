#!/usr/bin/env python3
"""
NeuroCode Codebase Parser Script.

Parses a Python codebase and populates the Neo4j graph.
Requires Python 3.11+.

Usage:
    python scripts/parse_codebase.py /path/to/python/project
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from parser.tree_sitter_parser import TreeSitterParser
from parser.relationship_extractor import RelationshipExtractor
from merkle.hash_calculator import HashCalculator
from graph_db.neo4j_client import Neo4jClient
from utils.config import get_settings
from utils.logger import configure_logging, get_logger


configure_logging()
logger = get_logger("parse_codebase")


async def parse_codebase(
    root_path: Path,
    clear_existing: bool = False,
    max_depth: int | None = None,
    include_variables: bool = True,
    exclude_tests: bool = False,
) -> dict:
    """
    Parse a Python codebase and store in Neo4j.

    Args:
        root_path: Path to the Python project
        clear_existing: Whether to clear existing graph data

    Returns:
        Dictionary with parsing statistics
    """
    settings = get_settings()
    start_time = time.perf_counter()

    # Find all Python files
    logger.info("scanning_for_python_files", path=str(root_path))

    python_files = list(root_path.rglob("*.py"))

    # Filter ignored patterns
    ignore_patterns = list(settings.parser.ignore_patterns)
    
    # Add test exclusion if requested
    if exclude_tests:
        ignore_patterns.extend(["test_", "tests/", "_test.py", "conftest.py"])

    def should_ignore(path: Path) -> bool:
        path_str = str(path)
        for pattern in ignore_patterns:
            if pattern in path_str:
                return True
        return False

    python_files = [f for f in python_files if not should_ignore(f)]

    logger.info("found_python_files", count=len(python_files))

    if not python_files:
        return {"error": "No Python files found"}

    # Parse all files
    parser = TreeSitterParser()
    hasher = HashCalculator()
    extractor = RelationshipExtractor()

    modules = []
    errors = []

    for i, file_path in enumerate(python_files):
        try:
            module = parser.parse_file(file_path)
            hasher.hash_tree(module)
            modules.append(module)

            if (i + 1) % 100 == 0:
                logger.info("parsing_progress", completed=i + 1, total=len(python_files))

        except Exception as e:
            errors.append(f"{file_path}: {e}")
            logger.warning("parse_error", path=str(file_path), error=str(e))

    parse_time = time.perf_counter() - start_time
    logger.info(
        "parsing_completed",
        modules=len(modules),
        errors=len(errors),
        time_seconds=round(parse_time, 2),
    )

    # Apply depth and variable filters to modules
    if max_depth is not None or not include_variables:
        for module in modules:
            # Filter variables if not included
            if not include_variables:
                module.variables = []
                for cls in module.classes:
                    cls.class_variables = []
                    cls.instance_variables = []
            
            # Apply depth filter
            # Depth 1 = modules only
            # Depth 2 = modules + classes
            # Depth 3 = modules + classes + methods/functions
            # Depth 4+ = everything
            if max_depth is not None:
                if max_depth < 2:
                    module.classes = []
                    module.functions = []
                elif max_depth < 3:
                    module.functions = []
                    for cls in module.classes:
                        cls.methods = []
    
    # Extract relationships
    logger.info("extracting_relationships")
    relationships = extractor.extract_relationships(modules)

    # Connect to Neo4j and store
    logger.info("connecting_to_neo4j")
    client = Neo4jClient()

    try:
        await client.connect()

        if clear_existing:
            logger.warning("clearing_existing_data")
            await client.clear_database()

        await client.initialize_schema()

        # Store nodes
        logger.info("storing_nodes")
        nodes_created = await client.bulk_create_nodes(modules)

        # Store relationships
        logger.info("storing_relationships")
        rels_created = await client.bulk_create_relationships(relationships)

        total_time = time.perf_counter() - start_time

        stats = {
            "status": "completed",
            "modules_parsed": len(modules),
            "nodes_created": nodes_created,
            "relationships_created": rels_created,
            "errors": errors,
            "parse_time_seconds": round(parse_time, 2),
            "total_time_seconds": round(total_time, 2),
        }

        logger.info("parsing_complete", **stats)
        return stats

    finally:
        await client.close()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Parse a Python codebase and populate the NeuroCode graph"
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Path to the Python project to parse",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing graph data before parsing",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum depth to parse (e.g., 2 = modules and classes, 3 = include methods)",
    )
    parser.add_argument(
        "--include-variables",
        action="store_true",
        default=False,
        help="Include module and class variables in the graph (can increase noise)",
    )
    parser.add_argument(
        "--exclude-tests",
        action="store_true",
        default=False,
        help="Exclude test directories from parsing",
    )

    args = parser.parse_args()

    if not args.path.exists():
        print(f"Error: Path does not exist: {args.path}")
        sys.exit(1)

    if not args.path.is_dir():
        print(f"Error: Path is not a directory: {args.path}")
        sys.exit(1)

    try:
        result = asyncio.run(parse_codebase(
            args.path, 
            clear_existing=args.clear,
            max_depth=args.max_depth,
            include_variables=args.include_variables,
            exclude_tests=args.exclude_tests,
        ))

        if "error" in result:
            print(f"Error: {result['error']}")
            sys.exit(1)

        print("\nParsing Complete!")
        print(f"  Modules parsed: {result['modules_parsed']}")
        print(f"  Nodes created: {result['nodes_created']}")
        print(f"  Relationships: {result['relationships_created']}")
        print(f"  Total time: {result['total_time_seconds']}s")

        if result["errors"]:
            print(f"\n  Errors: {len(result['errors'])}")
            for err in result["errors"][:5]:
                print(f"    - {err}")
            if len(result["errors"]) > 5:
                print(f"    ... and {len(result['errors']) - 5} more")

    except KeyboardInterrupt:
        print("\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
