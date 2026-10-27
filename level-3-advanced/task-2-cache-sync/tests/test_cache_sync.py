"""
Unit tests for CacheSync Write-Through Cache Coherence.
"""
import unittest
import os
import sys

# Ensure src is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from models import CacheEntry
from clock import TestClock
from storage import InMemoryBackingStore
from cache_manager import WriteThroughCacheManager


class TestCacheSync(unittest.TestCase):
    def setUp(self):
        self.clock = TestClock(initial_time=1000.0)
        self.backing_store = InMemoryBackingStore()
        # Initialize cache with small max_size=2 for easy eviction testing
        self.manager = WriteThroughCacheManager(
            backing_store=self.backing_store,
            clock=self.clock,
            max_size=2,
        )

    def test_basic_cache_hit_and_miss(self):
        """Writing and retrieving a key produces a cache hit."""
        self.manager.put("user_1", "Alice")
        self.assertEqual(self.manager.get("user_1"), "Alice")
        self.assertEqual(self.manager.stats.hits, 1)

    def test_bug_reproduction_ticket_cache_601_read_your_own_writes_buffer_bypass(self):
        """
        REPRODUCTION TEST 1 (Ticket #CACHE-601):
        Read-Your-Own-Writes Guarantee:
        If key A was written with value 'v2' but evicted from LRU before flush,
        a read of key A must still return 'v2' from the write buffer,
        NEVER the stale 'v1' from the backing store.
        """
        # Pre-seed persistent store with v1
        self.backing_store.write("profile_1", "Version 1 (Stale)")

        # Write v2 to cache (capacity is 2)
        self.manager.put("profile_1", "Version 2 (Fresh)")

        # Cause profile_1 to be evicted from LRU by adding 2 new keys (k2, k3)
        self.manager.put("k2", "val2")
        self.manager.put("k3", "val3")

        # Read profile_1 before flush() has been called
        # Must return Fresh Version 2 from dirty write buffer!
        result = self.manager.get("profile_1")
        self.assertEqual(
            result, "Version 2 (Fresh)",
            f"Read-your-own-writes violation! Returned stale value '{result}' instead of fresh buffered write."
        )

    def test_bug_reproduction_ticket_cache_602_dirty_key_eviction_data_loss(self):
        """
        REPRODUCTION TEST 2 (Ticket #CACHE-602):
        Dirty Key Eviction:
        When a dirty key is evicted from the in-memory LRU pool due to capacity constraints,
        its pending write must NOT be discarded from the write buffer. Calling flush()
        must successfully persist it to the backing store.
        """
        # Write k1 (dirty)
        self.manager.put("critical_data", "SecretValue")

        # Evict k1 by filling capacity with k2 and k3
        self.manager.put("filler_1", "f1")
        self.manager.put("filler_2", "f2")

        # Flush buffer to backing store
        flushed_count = self.manager.flush()

        # The backing store must contain critical_data!
        persisted_val = self.backing_store.read("critical_data")
        self.assertEqual(
            persisted_val, "SecretValue",
            "Data loss! Evicting a dirty key from LRU discarded its pending write to disk."
        )

    def test_bug_reproduction_ticket_cache_603_ttl_expiration_returns_none(self):
        """
        REPRODUCTION TEST 3 (Ticket #CACHE-603):
        When a key has a TTL (e.g. 10 seconds), reading it after 15 seconds
        must return None (cache miss), not the expired value.
        """
        self.manager.put("session_token", "active_tok_123", ttl_seconds=10.0)

        # Advance clock by 15 seconds
        self.clock.advance(15.0)

        val = self.manager.get("session_token")
        self.assertIsNone(
            val,
            f"TTL expiration ignored! Expected None for expired token, but got: {val}"
        )


if __name__ == "__main__":
    unittest.main()
