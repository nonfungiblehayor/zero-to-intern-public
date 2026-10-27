"""
CacheSync Write-Through Cache Manager.
"""
from typing import Any, Dict, Optional

try:
    from .models import CacheEntry, CacheStats
    from .clock import Clock, SystemClock
    from .storage import BackingStore, InMemoryBackingStore
    from .lru_cache import LRUCache
except ImportError:
    from models import CacheEntry, CacheStats
    from clock import Clock, SystemClock
    from storage import BackingStore, InMemoryBackingStore
    from lru_cache import LRUCache


class WriteThroughCacheManager:
    def __init__(
        self,
        backing_store: Optional[BackingStore] = None,
        clock: Optional[Clock] = None,
        max_size: int = 100,
    ):
        self.store = backing_store if backing_store is not None else InMemoryBackingStore()
        self.clock = clock if clock is not None else SystemClock()
        self.stats = CacheStats()

        # In-memory dirty write buffer holding pending writes before flush
        self._write_buffer: Dict[str, CacheEntry] = {}

        # Core LRU cache pool
        self._cache = LRUCache(max_size=max_size, on_evict=self._handle_eviction)

    def _handle_eviction(self, evicted_entry: CacheEntry) -> None:
        self.stats.evictions += 1
        # DEFECT (Ticket #CACHE-602): If the evicted entry is dirty, it is deleted from the write buffer
        # without being written to the backing store, leading to silent data loss!
        if evicted_entry.key in self._write_buffer:
            del self._write_buffer[evicted_entry.key]

    def get(self, key: str) -> Optional[Any]:
        if not key or not isinstance(key, str):
            raise ValueError("key must be a non-empty string")

        now = self.clock.now()

        # DEFECT (Ticket #CACHE-601): Fails to check _write_buffer before querying cache or backing store!
        # If an item was written to buffer and evicted from LRU, reading falls through to stale backing store.

        entry = self._cache.get(key)
        if entry is not None:
            # DEFECT (Ticket #CACHE-603): Ignores TTL expiration check on cache hit!
            # It returns the cached value even if entry.expires_at <= now.
            self.stats.hits += 1
            return entry.value

        # Cache miss - fallback to persistent backing store
        stored_val = self.store.read(key)
        if stored_val is not None:
            self.stats.misses += 1
            # Populate cache from persistent tier
            entry = CacheEntry(key=key, value=stored_val, created_at=now, expires_at=None, is_dirty=False)
            self._cache.put(entry)
            return stored_val

        self.stats.misses += 1
        return None

    def put(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        if not key or not isinstance(key, str):
            raise ValueError("key must be a non-empty string")

        now = self.clock.now()
        expires_at = now + ttl_seconds if ttl_seconds is not None else None

        entry = CacheEntry(
            key=key,
            value=value,
            created_at=now,
            expires_at=expires_at,
            is_dirty=True,
        )

        # Stage write into write buffer
        self._write_buffer[key] = entry
        # Store in LRU cache (may trigger eviction)
        self._cache.put(entry)

    def flush(self) -> int:
        """
        Commits all pending dirty writes in write buffer to backing store.
        Returns count of keys committed.
        """
        keys_flushed = len(self._write_buffer)
        for key, entry in list(self._write_buffer.items()):
            self.store.write(key, entry.value)
            entry.is_dirty = False
            del self._write_buffer[key]

        self.stats.flushes += keys_flushed
        return keys_flushed

    def get_pending_write_count(self) -> int:
        return len(self._write_buffer)
