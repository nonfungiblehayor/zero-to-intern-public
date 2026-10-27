"""
MetricStream Time-Series Data Models.
"""
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class MetricDataPoint:
    metric_name: str
    timestamp: float
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TimeWindow:
    start_time: float
    end_time: float

    def contains(self, timestamp: float) -> bool:
        # Standard half-open time interval [start_time, end_time)
        return self.start_time <= timestamp < self.end_time


@dataclass
class AggregatedBucket:
    metric_name: str
    window: TimeWindow
    count: int
    min_val: float
    max_val: float
    avg_val: float
    p95_val: float
