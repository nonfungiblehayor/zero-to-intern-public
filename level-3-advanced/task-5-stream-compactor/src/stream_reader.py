from typing import Optional, Dict, List
try:
    from .models import EventRecord
    from .segment import LogSegment
except ImportError:
    from models import EventRecord
    from segment import LogSegment


class PartitionStreamReader:
    def __init__(self, segments: List[LogSegment]):
        self.segments = segments

    def get_latest_state(self) -> Dict[str, str]:
        """
        Replays all segments from oldest to newest to compute materialized state.
        A tombstone deletes the key from the active materialized state.
        """
        state: Dict[str, str] = {}
        for seg in self.segments:
            for rec in seg.records:
                if rec.is_tombstone:
                    state.pop(rec.key, None)
                else:
                    state[rec.key] = rec.value
        return state

    def get_record(self, key: str) -> Optional[EventRecord]:
        """
        Searches newest to oldest segments for the most recent record of key.
        """
        for seg in reversed(self.segments):
            rec = seg.get(key)
            if rec is not None:
                return rec
        return None
