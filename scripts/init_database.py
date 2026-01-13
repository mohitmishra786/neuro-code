#!/usr/bin/env python3
"""
NeuroCode Database Initialization Script.

Initializes the Neo4j database with required schema.
Requires Python 3.11+.

Usage:
    python scripts/init_database.py
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from graph_db.neo4j_client import Neo4jClient
from graph_db.schema import GraphSchema
from utils.config import get_settings
from utils.logger import configure_logging, get_logger


configure_logging()
logger = get_logger("init_database")


async def init_database(clear: bool = False) -> None:
    """
    Initialize the Neo4j database.

    Args:
        clear: Whether to clear existing data first
    """
    settings = get_settings()
    logger.info(
        "initializing_database",
        uri=settings.neo4j.uri,
        database=settings.neo4j.database,
    )

    client = Neo4jClient()

    try:
        await client.connect()
        logger.info("connected_to_neo4j")

        if clear:
            logger.warning("clearing_existing_data")
            await client.clear_database()

        # Initialize schema
        logger.info("creating_schema")
        await client.initialize_schema()

        # Verify schema
        schema = GraphSchema()
        constraints = schema.get_constraint_statements()
        indexes = schema.get_index_statements()

        logger.info(
            "schema_initialized",
            constraints=len(constraints),
            indexes=len(indexes),
        )

        # Check database statistics
        query = """
        MATCH (n)
        RETURN labels(n) as label, count(*) as count
        """
        results = await client.execute_query(query)

        if results:
            for r in results:
                logger.info("node_count", label=r["label"], count=r["count"])
        else:
            logger.info("database_empty")

        print("\n✓ Database initialized successfully!")
        print(f"  URI: {settings.neo4j.uri}")
        print(f"  Database: {settings.neo4j.database}")

    except Exception as e:
        logger.error("initialization_failed", error=str(e))
        print(f"\n✗ Failed to initialize database: {e}")
        sys.exit(1)

    finally:
        await client.close()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize the NeuroCode Neo4j database"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before initialization",
    )

    args = parser.parse_args()

    try:
        asyncio.run(init_database(clear=args.clear))
    except KeyboardInterrupt:
        print("\nCancelled by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
