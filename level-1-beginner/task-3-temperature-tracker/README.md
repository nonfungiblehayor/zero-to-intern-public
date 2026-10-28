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

## Running the Application & Reproducing Defects

### Option A: Interactive Web UI (Visual Studio)

1. **Start the Backend API:**
   ```bash
   python3 api.py
   ```
2. **Start the Frontend Studio:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
3. Open `http://localhost:5173`. Click the preset scenario **"Ticket #WEATHER-301"** or **"Ticket #WEATHER-303"** to watch the sentinel bug and crash live in the UI!

### Option B: CLI Unit Tests

Run the test suite directly:
```bash
python3 -m unittest discover tests
```
Observe how the reproduction tests fail:
```
AssertionError: 0.0 != 18.5
ZeroDivisionError: division by zero
```

---

## Your Objectives

1. **Investigate the Codebase:**
   - Inspect `src/temperature_analyzer.py` and its corresponding test suite `tests/test_temperature_analyzer.py`.
2. **Diagnose Root Cause:**
   - Explain why `min_temp = 0.0` and `max_temp = 0.0` produce incorrect extrema.
   - Explain what causes `ZeroDivisionError` when calculating the average of an empty list.
3. **Implement the Fix:**
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
4. **Expand Test Coverage:**
   - Add tests covering single-element lists, uniform values, mixed integers and floats, rounding precision, and type validation.
5. **Prepare for Mentor Review:**
   - Be prepared to discuss sentinel values, edge cases, your fix, and test coverage during your technical interview.

---

## Rules and Guidelines

- Do not alter function signatures or expected output dictionary schema.
- Explain your technical findings and testing discipline clearly.
