"""
NeuroCode Merkle Tree Package.

Efficient change detection using content-based hashing.
Requires Python 3.11+.
"""

from merkle.change_detector import ChangeDetector
from merkle.hash_calculator import HashCalculator

__all__ = [
    "HashCalculator",
    "ChangeDetector",
]
