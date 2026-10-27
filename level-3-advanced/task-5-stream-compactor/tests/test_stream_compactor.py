import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from models import EventRecord
from segment import LogSegment
from compactor import StreamCompactor
from stream_reader import PartitionStreamReader


class TestStreamCompactor(unittest.TestCase):
    def setUp(self):
        self.compactor = StreamCompactor()

    def test_baseline_in_segment_key_deduplication(self):
        """Baseline: Compacting updates within a single segment keeps latest value."""
        seg = LogSegment(segment_id=1)
        seg.append(EventRecord("k1", "v1_init", offset=0, timestamp_ms=100))
        seg.append(EventRecord("k2", "v2_val", offset=1, timestamp_ms=101))
        seg.append(EventRecord("k1", "v1_updated", offset=2, timestamp_ms=102))

        compacted = self.compactor.compact_segments([seg])
        self.assertEqual(len(compacted.records), 2)
        rec_keys = [r.key for r in compacted.records]
        self.assertIn("k1", rec_keys)
        self.assertIn("k2", rec_keys)

    def test_bug_reproduction_ticket_stream_901_tombstone_purge_resurrects_older_record(self):
        """
        REPRODUCTION TEST 1 (Ticket #STREAM-901):
        Segment 0 (older) contains user1="Alice".
        Segment 1 contains tombstone user1=None (deleted).
        When Segment 1 is compacted while Segment 0 remains on disk,
        the tombstone must NOT be purged from the compacted segment!
        Purging it causes Alice to resurrect upon log replay!
        """
        seg0 = LogSegment(segment_id=0)
        seg0.append(EventRecord("user1", "Alice", offset=0, timestamp_ms=100))
        seg0.append(EventRecord("user2", "Bob", offset=1, timestamp_ms=101))

        seg1 = LogSegment(segment_id=1)
        seg1.append(EventRecord("user1", None, offset=2, timestamp_ms=200))  # Tombstone

        # Compact seg1 while seg0 is still an older uncompacted segment
        compacted_seg1 = self.compactor.compact_segments([seg1], older_segments=[seg0])

        # Tombstone must be retained in compacted_seg1
        rec_user1 = compacted_seg1.get("user1")
        self.assertIsNotNone(
            rec_user1,
            "Tombstone was purged prematurely! Older record will resurrect on replay."
        )
        self.assertTrue(rec_user1.is_tombstone)

        # Replay stream across [seg0, compacted_seg1]
        reader = PartitionStreamReader([seg0, compacted_seg1])
        state = reader.get_latest_state()
        self.assertNotIn(
            "user1", state,
            "Resurrection detected! Deleted user1 appeared in materialized stream state!"
        )
        self.assertEqual(state.get("user2"), "Bob")

    def test_bug_reproduction_ticket_stream_902_watermark_regression_lagging_consumer(self):
        """
        REPRODUCTION TEST 2 (Ticket #STREAM-902):
        Consumer A is at offset 500 (fast).
        Consumer B is at offset 50 (lagging).
        Safe watermark must be min(500, 50) = 50.
        Using max() sets watermark to 500, wiping unread events for Consumer B!
        """
        self.compactor.set_consumer_watermark("consumer-fast", 500)
        self.compactor.set_consumer_watermark("consumer-lagging", 50)

        safe_offset = self.compactor.get_safe_compaction_watermark()
        self.assertEqual(
            safe_offset, 50,
            "Watermark regression! Safe watermark must be minimum across consumers, not maximum!"
        )

    def test_bug_reproduction_ticket_stream_903_sparse_index_offset_map_corruption(self):
        """
        REPRODUCTION TEST 3 (Ticket #STREAM-903):
        Uncompacted segment has records at offsets 50, 60, 70 (length 3).
        In the compacted segment, records are stored at indices 0, 1, 2.
        The index must map key -> new position in records (0, 1, 2),
        NOT the old original offset (50, 60, 70), which causes IndexError!
        """
        seg = LogSegment(segment_id=5)
        seg.append(EventRecord("device:1", "active", offset=50, timestamp_ms=100))
        seg.append(EventRecord("device:2", "standby", offset=60, timestamp_ms=101))
        seg.append(EventRecord("device:3", "offline", offset=70, timestamp_ms=102))

        compacted = self.compactor.compact_segments([seg])

        # Attempt lookups by key using segment.get()
        try:
            r1 = compacted.get("device:1")
            r2 = compacted.get("device:2")
            r3 = compacted.get("device:3")
        except IndexError as e:
            self.fail(f"Index corrupted after compaction! Raised IndexError: {e}")

        self.assertIsNotNone(r1)
        self.assertEqual(r1.value, "active")
        self.assertEqual(r2.value, "standby")
        self.assertEqual(r3.value, "offline")


if __name__ == "__main__":
    unittest.main()
