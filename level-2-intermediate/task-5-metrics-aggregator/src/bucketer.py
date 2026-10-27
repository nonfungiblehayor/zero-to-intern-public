"""
MetricStream Time-Window Bucketer.
"""
import math
from typing import List

try:
    from .models import TimeWindow
except ImportError:
    from models import TimeWindow


class WindowBucketer:
    @staticmethod
    def align_timestamp(timestamp: float, window_seconds: int) -> float:
        """
        Floor aligns a timestamp to the nearest lower window boundary.
        e.g., timestamp=125.4, window=60 -> 120.0
        """
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        return float(math.floor(timestamp / window_seconds) * window_seconds)

    @staticmethod
    def get_window_for_timestamp(timestamp: float, window_seconds: int) -> TimeWindow:
        """
        Returns a half-open TimeWindow [start, start + window_seconds).
        """
        # DEFECT (Ticket #MET-501): Starter incorrectly uses <= boundary check or misaligns
        # points exactly on the boundary into the previous window.
        start = WindowBucketer.align_timestamp(timestamp, window_seconds)
        return TimeWindow(start_time=start, end_time=start + window_seconds)

    @staticmethod
    def generate_windows(start_time: float, end_time: float, window_seconds: int) -> List[TimeWindow]:
        """
        Generates contiguous sequence of TimeWindows covering [start_time, end_time).
        """
        if end_time <= start_time:
            return []

        first_window_start = WindowBucketer.align_timestamp(start_time, window_seconds)
        windows = []
        curr = first_window_start
        while curr < end_time:
            windows.append(TimeWindow(start_time=curr, end_time=curr + window_seconds))
            curr += window_seconds
        return windows
