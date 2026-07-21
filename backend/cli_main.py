"""
NeuroCode CLI entrypoint.

Usage (from backend/ or via package script):
    python -m cli_main parse /path/to/project
    neurocode parse /path/to/project
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path


def _ensure_backend_path() -> None:
    backend_root = Path(__file__).resolve().parent
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))
    # Also allow scripts/parse_codebase helpers
    repo_root = backend_root.parent
    scripts = repo_root / "scripts"
    if scripts.is_dir() and str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def main(argv: list[str] | None = None) -> int:
    """CLI main. Returns process exit code."""
    _ensure_backend_path()

    parser = argparse.ArgumentParser(
        prog="neurocode",
        description="NeuroCode — hierarchical knowledge graph for Python codebases",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    parse_p = sub.add_parser("parse", help="Parse a Python project into Neo4j")
    parse_p.add_argument("path", type=Path, help="Path to Python project root")
    parse_p.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing graph data before parse",
    )
    parse_p.add_argument(
        "--exclude-tests",
        action="store_true",
        help="Skip test files",
    )

    sub.add_parser("version", help="Print version")

    args = parser.parse_args(argv)

    if args.command == "version":
        from utils.config import get_settings

        print(get_settings().app_version)
        return 0

    if args.command == "parse":
        # Delegate to scripts/parse_codebase async entry
        repo_root = Path(__file__).resolve().parent.parent
        sys.path.insert(0, str(repo_root / "backend"))
        from scripts.parse_codebase import parse_codebase  # type: ignore[import-not-found]

        # parse_codebase lives under scripts — import via runpy fallback
        try:
            result = asyncio.run(
                _run_parse(args.path.resolve(), args.clear, args.exclude_tests)
            )
        except Exception as e:
            print(f"Parse failed: {e}", file=sys.stderr)
            return 1
        if result.get("error"):
            print(result["error"], file=sys.stderr)
            return 1
        print(
            f"Parsed {result.get('files_parsed', result.get('modules', '?'))} "
            f"in {result.get('elapsed_seconds', '?')}s"
        )
        return 0

    return 1


async def _run_parse(path: Path, clear: bool, exclude_tests: bool) -> dict:
    """Import parse_codebase from scripts directory."""
    import importlib.util

    repo_root = Path(__file__).resolve().parent.parent
    script = repo_root / "scripts" / "parse_codebase.py"
    spec = importlib.util.spec_from_file_location("parse_codebase_script", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {script}")
    mod = importlib.util.module_from_spec(spec)
    # Ensure backend on path before load
    sys.path.insert(0, str(repo_root / "backend"))
    spec.loader.exec_module(mod)
    return await mod.parse_codebase(
        path,
        clear_existing=clear,
        exclude_tests=exclude_tests,
    )


if __name__ == "__main__":
    raise SystemExit(main())
