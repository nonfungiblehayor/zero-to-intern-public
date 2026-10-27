from dataclasses import dataclass
from typing import Optional


@dataclass
class EventRecord:
    key: str
    value: Optional[str]
    offset: int
    timestamp_ms: int

    @property
    def is_tombstone(self) -> bool:
        return self.value is None


@dataclass
class SegmentMetadata:
    segment_id: int
    start_offset: int
    end_offset: int
    record_count: int
    is_compacted: bool = False
