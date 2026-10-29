# Candidate Brief: MetricStream Time-Series Aggregator
**Assessment ID:** `BH-L2-005`  
**[CANDIDATE MATERIAL]**

---

## Welcome to the Team

Welcome to the Telemetry & Observability engineering team at **MetricStream**. We operate the time-series pipeline that ingests system performance samples and rolls them up into continuous 1-minute analytical buckets for monitoring dashboards and alerting rules.

Our modular architecture coordinates telemetry downsampling across layers:
- `models.py`: Domain dataclasses (`MetricDataPoint`, `TimeWindow`, `AggregatedBucket`).
- `bucketer.py`: Time alignment and window interval generation.
- `aggregator.py`: Point ingestion and window aggregation engine.

Recently, our Site Reliability Engineers (SREs) and Dashboard teams escalated three critical production tickets:
- **Ticket #MET-501 (Boundary Fence-Post Defect):** Samples received at the exact second boundary (e.g., $t = 60.0\text{s}$) are incorrectly placed into the previous window $[0, 60)$ rather than the new window $[60, 120)$.
- **Ticket #MET-502 (Timeline Window Gap Suppression):** During quiet periods where a service records zero events in an interval, the aggregator drops the bucket entirely rather than returning a zero-filled record (`count=0, min=0.0, max=0.0, avg=0.0, p95=0.0`), breaking continuous charts in Grafana.
- **Ticket #MET-503 (Skewed P95 Percentile Calculations):** Percentile metrics report wild distortions because the calculation indexes into raw, unsorted sample arrays.

You are tasked with investigating where interval boundary comparison and statistical algorithms broke down, implementing an architecturally sound solution, and protecting our time-series engine against regressions.

---

## 🚀 Running the Fullstack Application & Tests

This task is configured as a **Fullstack Application (API + React UI)** with unit tests. You can test your changes using either the interactive web console or the automated test suite.

### Option A: Interactive Telemetry Studio (Web UI)
1. **Launch the Backend API Server:**
   ```bash
   python3 api.py
   ```
   *Runs on `http://localhost:8000` (FastAPI / Swagger docs at `/docs` if requirements installed, with built-in HTTP fallback).*

2. **Launch the Frontend Console:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   *Open `http://localhost:5173` in your browser.*
   - Ingest live metric samples and adjust downsampling intervals in real time.
   - Use the **1-Click Defect Reproduction Suite** to observe boundary fence-post traps, timeline gap suppression, and unsorted percentile calculations before and after your fix.

### Option B: Command-Line Test Suite
Run the test suite directly from the task root:
```bash
python3 -m unittest discover tests
```
Observe failures in:
- `test_bug_reproduction_ticket_met_501_boundary_fence_post`
- `test_bug_reproduction_ticket_met_502_missing_window_zero_fill`
- `test_bug_reproduction_ticket_met_503_p95_percentile_unsorted_sample`

---

## Your Objectives

1. **Investigate Codebase:**
   - Explore `src/`:
     - `models.py`: Domain dataclasses (`MetricDataPoint`, `TimeWindow`, `AggregatedBucket`).
     - `bucketer.py`: Time alignment and window interval generation.
     - `aggregator.py`: Point ingestion and window aggregation engine (**YOUR TASK IS HERE**).

2. **Analyze Root Causes:**
   - **Boundary Logic:** Why does `window.start_time <= p.timestamp <= window.end_time` cause points on the border to belong to the wrong window? Why are half-open intervals $[t_0, t_1)$ the industry standard for time-series aggregation?
   - **Timeline Continuity:** Why does Grafana break when empty intervals are dropped instead of zero-filled?
   - **Percentile Ranking:** What happens when nearest-rank index formulas are applied to an unsorted list of numbers?

3. **Implement the Fix:**
   - In `src/aggregator.py`:
     - Use half-open intervals: `window.contains(p.timestamp)` (or `window.start_time <= p.timestamp < window.end_time`).
     - When `fill_empty_windows=True` and no points fall into a window, return a zero-filled `AggregatedBucket(metric_name, window, count=0, min_val=0.0, max_val=0.0, avg_val=0.0, p95_val=0.0)`.
     - In `_calculate_p95`: Sort the values first (`sorted_vals = sorted(values)`). Compute nearest-rank index: `rank_idx = max(0, min(math.ceil(0.95 * len(sorted_vals)) - 1, len(sorted_vals) - 1))`.

4. **Expand Test Coverage:**
   - Add unit tests in `tests/test_metrics_aggregator.py` covering:
     - Sub-second timestamps and microsecond resolution.
     - Empty metric datasets with and without zero-fill enabled.
     - Large uniform distributions and edge-case percentile ranks.
     - Multi-metric isolation and independent time horizons.

5. **Prepare for Technical Defense:**
   - Be prepared to discuss time-series downsampling strategies, rollup intervals, memory management during sliding window evaluation, and percentiles vs averages during your technical interview.

---

## Rules and Guidelines

- Python 3 Standard Library only (`math`, `dataclasses`, `typing`).
- Do not alter public method signatures or dataclass definitions.
- Demonstrate clean engineering practices, statistical precision, and regression prevention.
