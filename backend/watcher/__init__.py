"""
NeuroCode File Watcher Package.

File system monitoring for incremental updates.
Requires Python 3.11+.
"""

from watcher.file_watcher import FileWatcher
from watcher.debouncer import Debouncer

__all__ = ["FileWatcher", "Debouncer"]
