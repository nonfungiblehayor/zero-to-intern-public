"""
MetricStream Time-Series Aggregator Service.
"""
import math
from typing import Dict, List, Optional
from collections import defaultdict

try:
    from .models import MetricDataPoint, TimeWindow, AggregatedBucket
    from .bucketer import WindowBucketer
except ImportError:
    from models import MetricDataPoint, TimeWindow, AggregatedBucket
    from bucketer import WindowBucketer


class MetricAggregator:
    def __init__(self, window_seconds: int = 60):
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self.window_seconds = window_seconds
        self._data_points: Dict[str, List[MetricDataPoint]] = defaultdict(list)

    def ingest(self, point: MetricDataPoint) -> None:
        if not point.metric_name:
            raise ValueError("metric_name cannot be empty")
        self._data_points[point.metric_name].append(point)

    def ingest_batch(self, points: List[MetricDataPoint]) -> None:
        for p in points:
            self.ingest(p)

    def aggregate_metric(
        self,
        metric_name: str,
        start_time: float,
        end_time: float,
        fill_empty_windows: bool = True,
    ) -> List[AggregatedBucket]:
        """
        Aggregates metric values into contiguous time windows across [start_time, end_time).
        """
        windows = WindowBucketer.generate_windows(start_time, end_time, self.window_seconds)
        points = self._data_points.get(metric_name, [])

        buckets = []

        for window in windows:
            matching_values = [
                p.value for p in points
                if window.start_time <= p.timestamp <= window.end_time
            ]

            if not matching_values:
                continue

            count = len(matching_values)
            min_val = min(matching_values)
            max_val = max(matching_values)
            avg_val = sum(matching_values) / count
            p95_val = self._calculate_p95(matching_values)

            buckets.append(
                AggregatedBucket(
                    metric_name=metric_name,
                    window=window,
                    count=count,
                    min_val=min_val,
                    max_val=max_val,
                    avg_val=round(avg_val, 4),
                    p95_val=round(p95_val, 4),
                )
            )

        return buckets

    def _calculate_p95(self, values: List[float]) -> float:
        """
        Calculates the 95th percentile value of the sample.
        """
        if not values:
            return 0.0

        idx = int(len(values) * 0.95)
        if idx >= len(values):
            idx = len(values) - 1
        return values[idx]
