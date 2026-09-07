"""
Source-conflict detection.

Surfaces disagreements between research sources -- the signal current
AI research tools smooth over. See detect.py for the detection
primitives and ``find_conflicts`` for the batch API used by the tool.
"""

from .detect import (
    Conflict,
    ConflictReport,
    ConflictType,
    find_conflicts,
)

__all__ = [
    "Conflict",
    "ConflictReport",
    "ConflictType",
    "find_conflicts",
]
