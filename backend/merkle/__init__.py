"""
NeuroCode Merkle Tree Package.

Efficient change detection using content-based hashing.
Requires Python 3.11+.
"""

from merkle.hash_calculator import HashCalculator
from merkle.change_detector import ChangeDetector

__all__ = [
    "HashCalculator",
    "ChangeDetector",
]
