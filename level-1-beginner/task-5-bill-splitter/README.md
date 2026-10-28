# Candidate Brief: Bug Hunt BH-L1-005
**[CANDIDATE MATERIAL]**

## 1. Engineering Scenario

You have joined the engineering team at **QuickSplit**, a restaurant bill and tip splitting service. Diners use QuickSplit to calculate tip percentages and figure out what each person owes.

Customer support escalated two issues:
1. **Ticket #PAY-501: Per-Person Amount Discrepancy & Missing Cents.**
   When 4 friends split a $50.00 check with a 15% tip ($7.50, total $57.50), the calculator displays $14.00 per person instead of $14.38. The restaurant was shorted $1.50!
2. **Ticket #PAY-502: Application Crash on Form Submission.**
   When web form inputs arrive as strings (`"60.00"`, `"3"`, `"20"`), the backend crashes with a 500 error (`TypeError: unsupported operand type(s) for /: 'str' and 'int'`).

Your goal is to investigate `src/bill_splitter.py`, fix both defects, add test cases covering edge cases (such as zero diners or non-numeric strings), and prepare to discuss your implementation during your technical interview.

---

## 2. Bug Report

- **Ticket IDs:** `PAY-501`, `PAY-502`
- **Severity:** High (Crash on Web Requests & Incorrect Payment Amounts)
- **Component:** `src/bill_splitter.py`

### Observed Behaviour
- `calculate_split(50.00, 4, 15)` returns `per_person: 14.0` instead of `14.38`.
- `calculate_split("60.00", "3", "20")` crashes with `TypeError`.
- `calculate_split(50.00, 0)` crashes with `ZeroDivisionError`.

### Expected Behaviour
- Support numeric inputs or numeric string inputs (e.g., `"50.00"`, `50.0`, `"4"`, `4`).
- Tip calculation: `round(bill * (tip_percent / 100.0), 2)`.
- Total with tip: `round(bill + tip_amount, 2)`.
- Individual share: `round(total_with_tip / num_people, 2)` (preserving decimal cents).
- Clean validation:
  - If `num_people < 1`, raise `ValueError`.
  - If `total_bill < 0` or `tip_percent < 0`, raise `ValueError`.
  - If input cannot be converted to a number (e.g. `"fifty"`), raise `ValueError`.

---

## 3. Setup & Running the Backend Service

This project is structured as a **Backend Service with REST Endpoints**.

### 1. Start the API Server:
```bash
python3 api.py
```
*The server starts on `http://localhost:8000` (FastAPI / Swagger documentation at `/docs` if requirements installed).*

### 2. Test the Endpoint via Curl:
```bash
curl -X POST http://localhost:8000/api/bill/split \
  -H "Content-Type: application/json" \
  -d '{"total_bill": 50.00, "num_people": 4, "tip_percent": 15}'
```
Observe that the response returns `per_person: 14.0` (missing the cents due to integer floor division).

Test string input handling:
```bash
curl -X POST http://localhost:8000/api/bill/split \
  -H "Content-Type: application/json" \
  -d '{"total_bill": "60.00", "num_people": "3", "tip_percent": "20"}'
```

### 3. CLI Unit Tests:
```bash
python3 -m unittest discover tests
```
Observed failures:
```
AssertionError: 14.0 != 14.38 : Per-person share must preserve decimal cents!
TypeError: unsupported operand type(s) for /: 'str' and 'int'
```

---

## 4. Candidate Objectives

1. **Investigate:** Trace the execution path in `src/bill_splitter.py` to identify why integer floor division `//` was used instead of true division `/`, and why string coercion was omitted.
2. **Fix:** Implement clean, robust input normalization and precise floating-point rounding.
3. **Test:**
   - Verify reproduction tests pass.
   - Add new tests in `tests/test_bill_splitter.py` covering edge cases (single diner, 0% tip, negative values, non-numeric strings).
4. **Prepare for Review:** Be prepared to explain your solution and design decisions during your mentor interview.
