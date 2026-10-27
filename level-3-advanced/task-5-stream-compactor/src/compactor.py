from typing import Dict, List, Optional, Set
try:
    from .models import EventRecord, SegmentMetadata
    from .segment import LogSegment
except ImportError:
    from models import EventRecord, SegmentMetadata
    from segment import LogSegment


class StreamCompactor:
    def __init__(self, start_compacted_id: int = 1000):
        self.next_compacted_id = start_compacted_id
        self.consumer_watermarks: Dict[str, int] = {}

    def set_consumer_watermark(self, consumer_id: str, offset: int):
        if not consumer_id:
            raise ValueError("consumer_id cannot be empty")
        if offset < 0:
            raise ValueError("offset cannot be negative")
        self.consumer_watermarks[consumer_id] = offset

    def get_safe_compaction_watermark(self) -> int:
        """
        Calculates the safe offset up to which compaction may occur.
        Compacting past unconsumed offsets destroys events for lagging consumers.
        """
        if not self.consumer_watermarks:
            return 0
        # BUG (Ticket #STREAM-902): Uses max instead of min across partition consumer offsets!
        # Lagging consumers have their unread events compacted away prematurely.
        return max(self.consumer_watermarks.values())

    def compact_segments(
        self,
        segments_to_compact: List[LogSegment],
        older_segments: Optional[List[LogSegment]] = None
    ) -> LogSegment:
        """
        Merges and compacts segments by retaining only the latest record for each key.
        """
        if not segments_to_compact:
            raise ValueError("segments_to_compact cannot be empty")

        latest_per_key: Dict[str, EventRecord] = {}
        for seg in segments_to_compact:
            for rec in seg.records:
                if rec.is_tombstone:
                    # BUG (Ticket #STREAM-901): Prematurely purges tombstones without checking
                    # if older uncompacted segments still contain this key!
                    # Discarding the tombstone causes older records to resurrect on log replay.
                    latest_per_key.pop(rec.key, None)
                else:
                    latest_per_key[rec.key] = rec

        compacted = LogSegment(segment_id=self.next_compacted_id)
        self.next_compacted_id += 1

        # Preserve deterministic offset order
        sorted_records = sorted(latest_per_key.values(), key=lambda r: r.offset)

        for new_pos, rec in enumerate(sorted_records):
            compacted_rec = EventRecord(
                key=rec.key,
                value=rec.value,
                offset=rec.offset,
                timestamp_ms=rec.timestamp_ms
            )
            compacted.records.append(compacted_rec)
            # BUG (Ticket #STREAM-903): Stores the old uncompacted offset (rec.offset)
            # instead of new_pos in compacted.records, corrupting segment.get(key) lookups!
            compacted.index[rec.key] = rec.offset

        return compacted
