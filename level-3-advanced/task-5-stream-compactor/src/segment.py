from typing import Optional, List, Dict, Set
try:
    from .models import EventRecord, SegmentMetadata
except ImportError:
    from models import EventRecord, SegmentMetadata


class LogSegment:
    def __init__(self, segment_id: int, max_records: int = 100):
        if segment_id < 0:
            raise ValueError("segment_id must be non-negative")
        self.segment_id = segment_id
        self.max_records = max_records
        self.records: List[EventRecord] = []
        self.index: Dict[str, int] = {}  # key -> position in self.records

    def append(self, record: EventRecord):
        if not record.key:
            raise ValueError("Record key cannot be empty")
        pos = len(self.records)
        self.records.append(record)
        self.index[record.key] = pos

    def get(self, key: str) -> Optional[EventRecord]:
        pos = self.index.get(key)
        if pos is None:
            return None
        if pos < 0 or pos >= len(self.records):
            raise IndexError(f"Index corrupted: position {pos} out of range (length {len(self.records)})")
        return self.records[pos]

    def is_full(self) -> bool:
        return len(self.records) >= self.max_records

    def get_keys(self) -> Set[str]:
        return set(self.index.keys())

    @property
    def start_offset(self) -> int:
        return self.records[0].offset if self.records else 0

    @property
    def end_offset(self) -> int:
        return self.records[-1].offset if self.records else 0

    def get_metadata(self, is_compacted: bool = False) -> SegmentMetadata:
        return SegmentMetadata(
            segment_id=self.segment_id,
            start_offset=self.start_offset,
            end_offset=self.end_offset,
            record_count=len(self.records),
            is_compacted=is_compacted
        )
