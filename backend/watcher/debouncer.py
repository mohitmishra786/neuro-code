"""
NeuroCode Debouncer.

Debounces rapid file system events.
Requires Python 3.11+.
"""

import asyncio
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from utils.logger import LoggerMixin


@dataclass
class PendingChange:
    """A pending file change waiting to be processed."""

    path: Path
    change_type: str  # created, modified, deleted
    timestamp: float


class Debouncer(LoggerMixin):
    """
    Debounces rapid file changes.

    Accumulates changes and triggers callback after a delay period
    with no new changes. This prevents processing the same file
    multiple times during rapid saves.
    """

    def __init__(
        self,
        delay_ms: int = 500,
        callback: Callable[[list[tuple[Path, str]]], Any] | None = None,
    ) -> None:
        """
        Initialize the debouncer.

        Args:
            delay_ms: Delay in milliseconds before processing
            callback: Function to call with accumulated changes
        """
        self._delay = delay_ms / 1000.0
        self._callback = callback
        self._pending: dict[Path, PendingChange] = {}
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_callback(self, callback: Callable[[list[tuple[Path, str]]], Any]) -> None:
        """Set or update the callback function."""
        self._callback = callback

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Set the event loop for async callbacks."""
        self._loop = loop

    def debounce(self, path: Path, change_type: str) -> None:
        """
        Add a file change to the pending queue.

        The callback will be triggered after delay_ms milliseconds
        of no new changes.

        Args:
            path: Path to the changed file
            change_type: Type of change (created, modified, deleted)
        """
        import time

        with self._lock:
            # Cancel existing timer
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None

            # Add or update pending change
            self._pending[path] = PendingChange(
                path=path,
                change_type=change_type,
                timestamp=time.time(),
            )

            # Start new timer
            self._timer = threading.Timer(self._delay, self._process_pending)
            self._timer.daemon = True
            self._timer.start()

    def _process_pending(self) -> None:
        """Process all pending changes."""
        with self._lock:
            if not self._pending:
                return

            # Collect all pending changes
            changes = [
                (change.path, change.change_type)
                for change in self._pending.values()
            ]
            self._pending.clear()
            self._timer = None

        self.log.debug("processing_debounced_changes", count=len(changes))

        # Call the callback
        if self._callback is not None:
            try:
                # Check if callback is async
                if asyncio.iscoroutinefunction(self._callback):
                    if self._loop is not None:
                        asyncio.run_coroutine_threadsafe(
                            self._callback(changes),
                            self._loop,
                        )
                    else:
                        # No event loop set, try to run in new loop
                        asyncio.run(self._callback(changes))
                else:
                    self._callback(changes)
            except Exception as e:
                self.log.error("debounce_callback_failed", error=str(e))

    def flush(self) -> list[tuple[Path, str]]:
        """
        Immediately process all pending changes.

        Returns:
            List of (path, change_type) tuples that were pending
        """
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None

            changes = [
                (change.path, change.change_type)
                for change in self._pending.values()
            ]
            self._pending.clear()

        if changes and self._callback is not None:
            try:
                if asyncio.iscoroutinefunction(self._callback):
                    if self._loop is not None:
                        asyncio.run_coroutine_threadsafe(
                            self._callback(changes),
                            self._loop,
                        )
                else:
                    self._callback(changes)
            except Exception as e:
                self.log.error("flush_callback_failed", error=str(e))

        return changes

    def clear(self) -> None:
        """Clear all pending changes without processing."""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            self._pending.clear()

    @property
    def pending_count(self) -> int:
        """Get number of pending changes."""
        return len(self._pending)

    @property
    def pending_paths(self) -> list[Path]:
        """Get list of paths with pending changes."""
        return list(self._pending.keys())


class AsyncDebouncer:
    """
    Async version of the debouncer for use in async contexts.

    Uses asyncio.Task instead of threading.Timer.
    """

    def __init__(
        self,
        delay_ms: int = 500,
        callback: Callable[[list[tuple[Path, str]]], Any] | None = None,
    ) -> None:
        """
        Initialize the async debouncer.

        Args:
            delay_ms: Delay in milliseconds before processing
            callback: Async function to call with accumulated changes
        """
        self._delay = delay_ms / 1000.0
        self._callback = callback
        self._pending: dict[Path, PendingChange] = {}
        self._task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

    def set_callback(self, callback: Callable[[list[tuple[Path, str]]], Any]) -> None:
        """Set or update the callback function."""
        self._callback = callback

    async def debounce(self, path: Path, change_type: str) -> None:
        """
        Add a file change to the pending queue.

        Args:
            path: Path to the changed file
            change_type: Type of change
        """
        import time

        async with self._lock:
            # Cancel existing task
            if self._task is not None and not self._task.done():
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass

            # Add pending change
            self._pending[path] = PendingChange(
                path=path,
                change_type=change_type,
                timestamp=time.time(),
            )

            # Start new task
            self._task = asyncio.create_task(self._wait_and_process())

    async def _wait_and_process(self) -> None:
        """Wait for delay then process pending changes."""
        await asyncio.sleep(self._delay)
        await self._process_pending()

    async def _process_pending(self) -> None:
        """Process all pending changes."""
        async with self._lock:
            if not self._pending:
                return

            changes = [
                (change.path, change.change_type)
                for change in self._pending.values()
            ]
            self._pending.clear()

        if self._callback is not None:
            try:
                if asyncio.iscoroutinefunction(self._callback):
                    await self._callback(changes)
                else:
                    self._callback(changes)
            except Exception:
                pass

    async def flush(self) -> list[tuple[Path, str]]:
        """Immediately process all pending changes."""
        async with self._lock:
            if self._task is not None and not self._task.done():
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass

            changes = [
                (change.path, change.change_type)
                for change in self._pending.values()
            ]
            self._pending.clear()

        if changes and self._callback is not None:
            if asyncio.iscoroutinefunction(self._callback):
                await self._callback(changes)
            else:
                self._callback(changes)

        return changes

    async def clear(self) -> None:
        """Clear all pending changes."""
        async with self._lock:
            if self._task is not None:
                self._task.cancel()
            self._pending.clear()
