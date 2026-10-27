"""
CacheSync Cache Coherence Domain Models.
"""
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: float
    expires_at: Optional[float] = None
    is_dirty: bool = False


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    flushes: int = 0
