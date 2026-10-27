# Candidate Brief: Bug Hunt BH-L1-004
**[CANDIDATE MATERIAL]**

## 1. Engineering Scenario

You have joined the software team at **EduGrade**, a learning platform that calculates course grades, GPA scores, and academic report cards for schools.

A teacher reported an alarming issue:
**Ticket #EDU-401: Honour Roll Students Assigned Grade 'D' on Report Cards**.

Top-ranking students who earned scores of 95% and 85% received a 'D' on their official transcripts!
Your task is to investigate `src/grade_calculator.py`, reproduce the error, fix the root cause, verify boundary scores with tests, and submit your technical report.

---

## 2. Bug Report

- **Ticket ID:** `EDU-401`
- **Reporter:** Academic Registrar
- **Severity:** High (Incorrect Student Transcripts)
- **Component:** `src/grade_calculator.py`

### Observed Behaviour
- Student scoring 95.0% receives letter grade **'D'** (GPA 1.0).
- Student scoring 85.0% receives letter grade **'D'** (GPA 1.0).
- Student scoring 75.0% receives letter grade **'D'** (GPA 1.0).

### Expected Behaviour
- 90.0% to 100.0%: **'A'** (GPA 4.0, Passing)
- 80.0% to 89.9%: **'B'** (GPA 3.0, Passing)
- 70.0% to 79.9%: **'C'** (GPA 2.0, Passing)
- 60.0% to 69.9%: **'D'** (GPA 1.0, Not Passing)
- Below 60.0%: **'F'** (GPA 0.0, Not Passing)

---

## 3. Business Rules Specification

1. **Grade Thresholds:**
   - Score >= 90.0 -> `'A'`
   - 80.0 <= Score < 90.0 -> `'B'`
   - 70.0 <= Score < 80.0 -> `'C'`
   - 60.0 <= Score < 70.0 -> `'D'`
   - Score < 60.0 -> `'F'`
2. **Extra Credit:**
   - If `has_extra_credit` is `True`, add 5.0 points to the score.
   - The final score with extra credit must be capped at 100.0 max.
3. **Validation:**
   - `score` must be a numeric integer or float. Otherwise raise `TypeError`.
   - `score` must be within range 0.0 to 100.0 (inclusive). Otherwise raise `ValueError`.
   - `student_name` must be a non-empty string. Otherwise raise `ValueError`.

---

## 4. Setup & Reproduction

```bash
cd starter_repo
python3 -m unittest discover tests
```
Observed failure:
```
AssertionError: 'D' != 'A' : High scores >= 90 must receive an 'A'!
```
