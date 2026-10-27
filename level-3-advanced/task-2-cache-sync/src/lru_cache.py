"""
LRU Cache Data Structure with Eviction Callback.
"""
from collections import OrderedDict
from typing import Any, Callable, Dict, Optional, Tuple

try:
    from .models import CacheEntry
except ImportError:
    from models import CacheEntry


class LRUCache:
    def __init__(self, max_size: int = 100, on_evict: Optional[Callable[[CacheEntry], None]] = None):
        if max_size <= 0:
            raise ValueError("max_size must be positive")
        self.max_size = max_size
        self._entries: OrderedDict[str, CacheEntry] = OrderedDict()
        self._on_evict = on_evict

    def get(self, key: str) -> Optional[CacheEntry]:
        if key not in self._entries:
            return None
        # Move accessed entry to end (most recently used)
        self._entries.move_to_end(key)
        return self._entries[key]

    def peek(self, key: str) -> Optional[CacheEntry]:
        """Inspect without updating LRU order."""
        return self._entries.get(key)

    def put(self, entry: CacheEntry) -> Optional[CacheEntry]:
        """
        Inserts or updates an entry. If capacity is exceeded, evicts the least recently used item.
        Returns the evicted entry if eviction occurred, else None.
        """
        evicted = None
        if entry.key in self._entries:
            self._entries.move_to_end(entry.key)
        self._entries[entry.key] = entry

        if len(self._entries) > self.max_size:
            # Pop least recently used (first item)
            evicted_key, evicted_entry = self._entries.popitem(last=False)
            evicted = evicted_entry
            if self._on_evict:
                self._on_evict(evicted_entry)

        return evicted

    def remove(self, key: str) -> Optional[CacheEntry]:
        return self._entries.pop(key, None)

    def __len__(self) -> int:
        return len(self._entries)

    def contains(self, key: str) -> bool:
        return key in self._entries
