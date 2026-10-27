"""
Unit tests for MetricStream Time-Series Aggregator.
"""
import unittest
import os
import sys

# Ensure src is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from models import MetricDataPoint, TimeWindow
from bucketer import WindowBucketer
from aggregator import MetricAggregator


class TestMetricAggregator(unittest.TestCase):
    def setUp(self):
        self.aggregator = MetricAggregator(window_seconds=60)

    def test_basic_aggregation(self):
        """Points within a window are aggregated accurately."""
        points = [
            MetricDataPoint("cpu_usage", 10.0, 40.0),
            MetricDataPoint("cpu_usage", 20.0, 60.0),
            MetricDataPoint("cpu_usage", 50.0, 50.0),
        ]
        self.aggregator.ingest_batch(points)
        buckets = self.aggregator.aggregate_metric("cpu_usage", 0.0, 60.0)

        self.assertEqual(len(buckets), 1)
        b = buckets[0]
        self.assertEqual(b.count, 3)
        self.assertEqual(b.min_val, 40.0)
        self.assertEqual(b.max_val, 60.0)
        self.assertEqual(b.avg_val, 50.0)

    def test_bug_reproduction_ticket_met_501_boundary_fence_post(self):
        """
        REPRODUCTION TEST 1 (Ticket #MET-501):
        Time windows are half-open intervals [start, end).
        A point at timestamp exactly 60.0 belongs to window [60, 120),
        NOT window [0, 60).
        """
        # Exactly on the 60.0s boundary
        self.aggregator.ingest(MetricDataPoint("api_latency", 60.0, 120.0))
        buckets = self.aggregator.aggregate_metric("api_latency", 0.0, 120.0, fill_empty_windows=True)

        self.assertEqual(len(buckets), 2)
        window_0_60 = buckets[0]
        window_60_120 = buckets[1]

        self.assertEqual(
            window_0_60.count, 0,
            "Boundary fence-post error: Point at 60.0s was included in window [0, 60)!"
        )
        self.assertEqual(
            window_60_120.count, 1,
            "Point at 60.0s was missing from window [60, 120)!"
        )

    def test_bug_reproduction_ticket_met_502_missing_window_zero_fill(self):
        """
        REPRODUCTION TEST 2 (Ticket #MET-502):
        When fill_empty_windows=True, intermediate windows with zero samples
        must be retained with count=0 and zeroed metrics, preserving a continuous timeline.
        """
        # Event at t=10.0 (Window [0, 60)) and t=130.0 (Window [120, 180)). Window [60, 120) has no events.
        self.aggregator.ingest(MetricDataPoint("req_count", 10.0, 1.0))
        self.aggregator.ingest(MetricDataPoint("req_count", 130.0, 1.0))

        buckets = self.aggregator.aggregate_metric("req_count", 0.0, 180.0, fill_empty_windows=True)

        self.assertEqual(
            len(buckets), 3,
            f"Expected 3 continuous windows (including empty window), but got {len(buckets)}!"
        )
        empty_bucket = buckets[1]
        self.assertEqual(empty_bucket.window.start_time, 60.0)
        self.assertEqual(empty_bucket.count, 0)
        self.assertEqual(empty_bucket.avg_val, 0.0)

    def test_bug_reproduction_ticket_met_503_p95_percentile_unsorted_sample(self):
        """
        REPRODUCTION TEST 3 (Ticket #MET-503):
        Calculating the 95th percentile on an unsorted stream of values
        must sort the distribution prior to index extraction.
        """
        # 20 samples from 1 to 20, deliberately shuffled: high values at the beginning
        shuffled_values = [20.0, 19.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0]
        for idx, val in enumerate(shuffled_values):
            self.aggregator.ingest(MetricDataPoint("test_metric", 10.0 + idx, val))

        buckets = self.aggregator.aggregate_metric("test_metric", 0.0, 60.0)
        self.assertEqual(len(buckets), 1)
        b = buckets[0]

        # 95th percentile of 1..20 is 19.0 or 20.0 (depending on rank).
        # Unsorted code accesses index 19 of original list which has value 18.0!
        self.assertGreaterEqual(
            b.p95_val, 19.0,
            f"Unsorted percentile calculation error: got {b.p95_val}, expected >= 19.0"
        )


if __name__ == "__main__":
    unittest.main()
