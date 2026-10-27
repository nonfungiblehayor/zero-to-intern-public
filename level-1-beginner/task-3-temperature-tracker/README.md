# Candidate Brief: WeatherStation Temperature Analyzer
**Assessment ID:** `BH-L1-003`  
**[CANDIDATE MATERIAL]**

---

## Welcome to the Team

Welcome to the data engineering team at **WeatherStation**. We maintain the telemetry processors that ingest and analyze daily temperature readings reported by IoT environmental sensors worldwide.

Recent monitoring alerts from our operations team highlighted three critical bugs in our temperature analysis pipeline:
1. **Ticket #STATION-101:** During warm summer periods, sensors reporting warm temperatures (e.g., `[18.5, 22.0, 25.4]`) output a minimum temperature of `0.0°C`, leading automated agricultural monitors to sound false frost warnings.
2. **Ticket #STATION-102:** In winter weather stations reporting sub-zero temperatures (e.g., `[-15.0, -8.2, -3.5]`), the maximum temperature is reported as `0.0°C` instead of `-3.5°C`.
3. **Ticket #STATION-103:** When newly installed or offline sensors send an empty list of readings (`[]`), the data processor crashes with an unhandled `ZeroDivisionError`.

You are assigned to investigate, reproduce, and fix these issues in our analyzer module.

---

## Your Objectives

1. **Investigate the Codebase:**
   - Inspect `src/temperature_analyzer.py` and its corresponding test suite `tests/test_temperature_analyzer.py`.
2. **Reproduce the Bugs:**
   - Run the test suite:
     ```bash
     python3 -m unittest discover tests
     ```
   - Observe how `test_bug_reproduction_all_warm_readings_min_zero`, `test_bug_reproduction_all_subzero_readings_max_zero`, and `test_bug_reproduction_empty_readings_division_by_zero` fail.
3. **Diagnose Root Cause:**
   - Explain why `min_temp = 0.0` and `max_temp = 0.0` produce incorrect extrema.
   - Explain what causes `ZeroDivisionError` when calculating the average of an empty list.
4. **Implement the Fix:**
   - Modify `src/temperature_analyzer.py` to correctly calculate minimum, maximum, and average values.
   - For an empty reading list, return a safe dictionary with:
     ```python
     {
         "min_temp": None,
         "max_temp": None,
         "avg_temp": None,
         "reading_count": 0,
         "is_freezing": False
     }
     ```
5. **Expand Test Coverage:**
   - Add tests covering single-element lists, uniform values, mixed integers and floats, rounding precision, and type validation.
6. **Submit Documentation:**
   - Fill out [CANDIDATE_SUBMISSION.md](file:///home/l2e/Documents/talent-nation/zero-to-intern/Bug-Hunt/level-1-beginner/task-3-temperature-tracker/starter_repo/CANDIDATE_SUBMISSION.md).

---

## Rules and Guidelines

- Do not introduce external dependencies. Use Python 3 Standard Library only.
- Maintain the exact return dictionary keys: `"min_temp"`, `"max_temp"`, `"avg_temp"`, `"reading_count"`, `"is_freezing"`.
- Document your findings clearly in the submission form.
