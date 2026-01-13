"""
NeuroCode File Watcher.

Cross-platform file system monitoring using watchdog.
Requires Python 3.11+.
"""

import asyncio
import fnmatch
from collections.abc import Callable
from pathlib import Path
from typing import Any

from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler,
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
    FileMovedEvent,
    DirCreatedEvent,
    DirDeletedEvent,
    DirModifiedEvent,
    DirMovedEvent,
)

from watcher.debouncer import Debouncer
from utils.config import get_settings
from utils.logger import LoggerMixin


class PythonFileHandler(FileSystemEventHandler, LoggerMixin):
    """
    Handles file system events for Python files.

    Filters events to only Python files and ignores specified patterns.
    """

    def __init__(
        self,
        debouncer: Debouncer,
        ignore_patterns: list[str] | None = None,
    ) -> None:
        """
        Initialize the file handler.

        Args:
            debouncer: Debouncer to accumulate changes
            ignore_patterns: Glob patterns to ignore
        """
        super().__init__()
        self._debouncer = debouncer
        self._ignore_patterns = ignore_patterns or []

    def _should_ignore(self, path: str) -> bool:
        """Check if a path should be ignored."""
        for pattern in self._ignore_patterns:
            if pattern in path or fnmatch.fnmatch(path, pattern):
                return True
        return False

    def _is_python_file(self, path: str) -> bool:
        """Check if path is a Python file."""
        return path.endswith(".py")

    def on_created(self, event: FileCreatedEvent | DirCreatedEvent) -> None:
        """Handle file/directory creation."""
        if isinstance(event, DirCreatedEvent):
            return

        path = event.src_path
        if not self._is_python_file(path) or self._should_ignore(path):
            return

        self.log.debug("file_created", path=path)
        self._debouncer.debounce(Path(path), "created")

    def on_modified(self, event: FileModifiedEvent | DirModifiedEvent) -> None:
        """Handle file/directory modification."""
        if isinstance(event, DirModifiedEvent):
            return

        path = event.src_path
        if not self._is_python_file(path) or self._should_ignore(path):
            return

        self.log.debug("file_modified", path=path)
        self._debouncer.debounce(Path(path), "modified")

    def on_deleted(self, event: FileDeletedEvent | DirDeletedEvent) -> None:
        """Handle file/directory deletion."""
        if isinstance(event, DirDeletedEvent):
            return

        path = event.src_path
        if not self._is_python_file(path) or self._should_ignore(path):
            return

        self.log.debug("file_deleted", path=path)
        self._debouncer.debounce(Path(path), "deleted")

    def on_moved(self, event: FileMovedEvent | DirMovedEvent) -> None:
        """Handle file/directory move/rename."""
        if isinstance(event, DirMovedEvent):
            return

        src_path = event.src_path
        dest_path = event.dest_path

        # Handle source as deleted
        if self._is_python_file(src_path) and not self._should_ignore(src_path):
            self.log.debug("file_moved_from", path=src_path)
            self._debouncer.debounce(Path(src_path), "deleted")

        # Handle destination as created
        if self._is_python_file(dest_path) and not self._should_ignore(dest_path):
            self.log.debug("file_moved_to", path=dest_path)
            self._debouncer.debounce(Path(dest_path), "created")


class FileWatcher(LoggerMixin):
    """
    Watches a directory for Python file changes.

    Uses watchdog for cross-platform file system monitoring
    with debouncing to prevent excessive updates during rapid saves.
    """

    def __init__(
        self,
        root_path: Path,
        on_change: Callable[[list[tuple[Path, str]]], Any] | None = None,
        debounce_delay_ms: int | None = None,
        ignore_patterns: list[str] | None = None,
        recursive: bool = True,
    ) -> None:
        """
        Initialize the file watcher.

        Args:
            root_path: Root directory to watch
            on_change: Callback for batched changes (path, change_type)
            debounce_delay_ms: Debounce delay in milliseconds
            ignore_patterns: Glob patterns to ignore
            recursive: Whether to watch subdirectories
        """
        settings = get_settings()

        self._root_path = root_path
        self._recursive = recursive
        self._ignore_patterns = ignore_patterns or settings.parser.ignore_patterns
        self._debounce_delay = debounce_delay_ms or settings.watcher.debounce_delay_ms

        self._debouncer = Debouncer(
            delay_ms=self._debounce_delay,
            callback=on_change,
        )

        self._handler = PythonFileHandler(
            debouncer=self._debouncer,
            ignore_patterns=self._ignore_patterns,
        )

        self._observer: Observer | None = None
        self._running = False

    def set_callback(self, callback: Callable[[list[tuple[Path, str]]], Any]) -> None:
        """Set or update the change callback."""
        self._debouncer.set_callback(callback)

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Set the event loop for async callbacks."""
        self._debouncer.set_event_loop(loop)

    def start(self) -> None:
        """Start watching for file changes."""
        if self._running:
            return

        self._observer = Observer()
        self._observer.schedule(
            self._handler,
            str(self._root_path),
            recursive=self._recursive,
        )
        self._observer.start()
        self._running = True

        self.log.info(
            "file_watcher_started",
            path=str(self._root_path),
            recursive=self._recursive,
            ignore_patterns=self._ignore_patterns,
        )

    def stop(self) -> None:
        """Stop watching for file changes."""
        if not self._running:
            return

        # Flush any pending changes
        self._debouncer.flush()

        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5.0)
            self._observer = None

        self._running = False
        self.log.info("file_watcher_stopped")

    def flush(self) -> list[tuple[Path, str]]:
        """Immediately process any pending changes."""
        return self._debouncer.flush()

    @property
    def is_running(self) -> bool:
        """Check if the watcher is running."""
        return self._running

    @property
    def pending_count(self) -> int:
        """Get number of pending changes."""
        return self._debouncer.pending_count

    def __enter__(self) -> "FileWatcher":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.stop()


async def create_async_watcher(
    root_path: Path,
    on_change: Callable[[list[tuple[Path, str]]], Any],
    debounce_delay_ms: int | None = None,
) -> FileWatcher:
    """
    Create a file watcher configured for async operation.

    Args:
        root_path: Root directory to watch
        on_change: Async callback for changes
        debounce_delay_ms: Debounce delay in milliseconds

    Returns:
        Configured FileWatcher instance
    """
    watcher = FileWatcher(
        root_path=root_path,
        on_change=on_change,
        debounce_delay_ms=debounce_delay_ms,
    )
    watcher.set_event_loop(asyncio.get_event_loop())
    return watcher
