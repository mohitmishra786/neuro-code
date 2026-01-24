#!/usr/bin/env python3
"""
NeuroCode Deep Parser Script.

Uses the 3-pass ProjectParser for deep cross-file symbol resolution.
Requires Python 3.11+.

Usage:
    python scripts/parse_deep.py /path/to/python/project
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from parser.project_parser import ProjectParser
from graph_db.neo4j_client import Neo4jClient
from utils.config import get_settings
from utils.logger import configure_logging, get_logger


configure_logging()
logger = get_logger("parse_deep")


async def parse_project(
    root_path: Path,
    clear_existing: bool = False,
) -> dict:
    """
    Parse a Python project using deep symbol resolution.

    Args:
        root_path: Path to the Python project
        clear_existing: Whether to clear existing graph data

    Returns:
        Dictionary with parsing statistics
    """
    start_time = time.perf_counter()
    
    logger.info("starting_deep_parse", path=str(root_path))
    
    # Initialize the project parser
    parser = ProjectParser(root_path)
    
    # Execute 3-pass parsing
    packages, modules, relationships = parser.parse_project()
    
    parse_time = time.perf_counter() - start_time
    
    logger.info(
        "parsing_completed",
        packages=len(packages),
        modules=len(modules),
        relationships=len(relationships),
        errors=len(parser.errors),
        symbols=len(parser.symbols),
        time_seconds=round(parse_time, 2),
    )
    
    if not modules and not packages:
        return {"error": "No modules parsed", "errors": parser.errors}
    
    # Connect to Neo4j and store
    logger.info("connecting_to_neo4j")
    client = Neo4jClient()
    
    try:
        await client.connect()
        
        if clear_existing:
            logger.warning("clearing_existing_data")
            await client.clear_database()
        
        await client.initialize_schema()
        
        # Store packages first
        logger.info("storing_packages", count=len(packages))
        packages_created = await client.bulk_create_packages(packages)
        
        # Store nodes
        logger.info("storing_nodes", count=len(modules))
        nodes_created = await client.bulk_create_nodes(modules)
        
        # Store relationships
        logger.info("storing_relationships", count=len(relationships))
        rels_created = await client.bulk_create_relationships(relationships)
        
        total_time = time.perf_counter() - start_time
        
        # Count cross-file edges
        cross_file_calls = sum(
            1 for r in relationships 
            if r.relationship_type.value == "calls" and "::" in r.source_id
        )
        
        stats = {
            "status": "completed",
            "packages_created": packages_created,
            "modules_parsed": len(modules),
            "nodes_created": nodes_created,
            "relationships_created": rels_created,
            "symbols_resolved": len(parser.symbols),
            "cross_file_calls": cross_file_calls,
            "errors": parser.errors,
            "parse_time_seconds": round(parse_time, 2),
            "total_time_seconds": round(total_time, 2),
        }
        
        logger.info("parsing_complete", **stats)
        return stats
    
    finally:
        await client.close()


def main() -> None:
    """Main entry point."""
    arg_parser = argparse.ArgumentParser(
        description="Deep-parse a Python codebase with cross-file symbol resolution"
    )
    arg_parser.add_argument(
        "path",
        type=Path,
        help="Path to the Python project to parse",
    )
    arg_parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing graph data before parsing",
    )
    arg_parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum depth to parse (e.g., 2 = packages/modules and classes, 3 = include methods)",
    )
    arg_parser.add_argument(
        "--include-variables",
        action="store_true",
        default=False,
        help="Include module and class variables in the graph (can increase noise)",
    )
    
    args = arg_parser.parse_args()
    
    if not args.path.exists():
        print(f"Error: Path does not exist: {args.path}")
        sys.exit(1)
    
    if not args.path.is_dir():
        print(f"Error: Path is not a directory: {args.path}")
        sys.exit(1)
    
    try:
        result = asyncio.run(parse_project(args.path, clear_existing=args.clear))
        
        if "error" in result:
            print(f"Error: {result['error']}")
            if result.get("errors"):
                for err in result["errors"][:5]:
                    print(f"  - {err}")
            sys.exit(1)
        
        print("\nDeep Parsing Complete!")
        print(f"  Packages created: {result['packages_created']}")
        print(f"  Modules parsed: {result['modules_parsed']}")
        print(f"  Nodes created: {result['nodes_created']}")
        print(f"  Relationships: {result['relationships_created']}")
        print(f"  Symbols resolved: {result['symbols_resolved']}")
        print(f"  Cross-file calls: {result['cross_file_calls']}")
        print(f"  Parse time: {result['parse_time_seconds']}s")
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
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
