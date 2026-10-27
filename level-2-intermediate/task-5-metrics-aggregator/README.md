# Candidate Brief: MetricStream Time-Series Aggregator
**Assessment ID:** `BH-L2-005`  
**[CANDIDATE MATERIAL]**

---

## Welcome to MetricStream

Welcome to the Telemetry & Observability engineering team at **MetricStream**. We operate the time-series pipeline that ingests system performance samples and rolls them up into continuous 1-minute analytical buckets for monitoring dashboards and alerting rules.

Recently, our Site Reliability Engineers (SREs) and Dashboard teams escalated three critical defects:
- **Ticket #MET-501 (Boundary Double-Counting / Fence-Post Defect):** Samples received at the exact second boundary (e.g. $t = 60.0$) are incorrectly placed into the previous window $[0, 60)$ rather than the new window $[60, 120)$.
- **Ticket #MET-502 (Missing Timeline Gaps):** During quiet periods where a service records zero events in a 1-minute interval, the aggregator drops the bucket entirely rather than returning a zero-filled record (`count=0, min=0.0, max=0.0, avg=0.0, p95=0.0`), breaking continuous charts in Grafana.
- **Ticket #MET-503 (Skewed P95 Percentile Calculations):** Percentile metrics report wild distortions because the calculation indexes into raw, unsorted arrays.

You are tasked with investigating the codebase, correcting the interval boundary comparison and statistical algorithms, and safeguarding the time-series engine with unit tests.

---

## Your Objectives

1. **Investigate Codebase:**
   - `src/models.py`: Domain dataclasses (`MetricDataPoint`, `TimeWindow`, `AggregatedBucket`).
   - `src/bucketer.py`: Time alignment and window interval generation.
   - `src/aggregator.py`: Point ingestion and window aggregation engine.
2. **Reproduce the Defect:**
   ```bash
   python3 -m unittest discover tests
   ```
   Observe the failures in:
   - `test_bug_reproduction_ticket_met_501_boundary_fence_post`
   - `test_bug_reproduction_ticket_met_502_missing_window_zero_fill`
   - `test_bug_reproduction_ticket_met_503_p95_percentile_unsorted_sample`
3. **Analyze Root Causes:**
   - **Boundary Logic:** Why does `window.start_time <= p.timestamp <= window.end_time` cause points on the border to belong to the wrong window?
   - **Timeline Continuity:** Why does Grafana break when empty intervals are dropped instead of zero-filled?
   - **Percentile Ranking:** What happens when an index formula is applied to an unsorted list of numbers?
4. **Implement the Fix:**
   - In `src/aggregator.py`:
     - Use half-open intervals: `window.contains(p.timestamp)` (or `window.start_time <= p.timestamp < window.end_time`).
     - When `fill_empty_windows=True` and no points fall into a window, return a zero-filled `AggregatedBucket(metric_name, window, count=0, min_val=0.0, max_val=0.0, avg_val=0.0, p95_val=0.0)`.
     - In `_calculate_p95`: Sort the values: `sorted_vals = sorted(values)`. Compute nearest-rank index: `rank_idx = max(0, min(math.ceil(0.95 * len(sorted_vals)) - 1, len(sorted_vals) - 1))`.
5. **Add Unit Tests:**
   - Expand `tests/test_metrics_aggregator.py` to cover sub-second timestamps, empty datasets, large uniform distributions, and multi-metric isolation.
6. **Complete Documentation:**
   - Fill out all sections in [CANDIDATE_SUBMISSION.md](file:///home/l2e/Documents/talent-nation/zero-to-intern/Bug-Hunt/level-2-intermediate/task-5-metrics-aggregator/starter_repo/CANDIDATE_SUBMISSION.md).

---

## Rules and Guidelines

- Python 3 Standard Library only. Do not install external libraries.
- Do not alter public method signatures or dataclass definitions.
- Document all mathematical decisions in `CANDIDATE_SUBMISSION.md`.
