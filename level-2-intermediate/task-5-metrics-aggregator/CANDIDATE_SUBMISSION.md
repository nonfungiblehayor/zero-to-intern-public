# Candidate Submission Form: Bug Hunt BH-L2-005
**[CANDIDATE MATERIAL]**

Please complete this form before submitting your assessment. Be concise, precise, and technical.

---

### Candidate Information
- **Candidate Name:**
- **Submission Date:**
- **Time Spent (minutes):**

---

### 1. Root-Cause Analysis
*What was the root cause of the bugs reported in Tickets #MET-501, #MET-502, and #MET-503? Explain why half-open intervals [start, end) are necessary in time-series aggregations, and why percentile computations require sorted distributions.*

> [Write your answer here]

---

### 2. Implementation Summary
*What specific changes did you make in `src/bucketer.py` and `src/aggregator.py` to fix interval boundary placement, empty window zero-filling, and p95 percentile calculations?*

> [Write your answer here]

---

### 3. Solution Justification & Numerical Precision
*How does your corrected logic guarantee that timestamps on exact window boundaries are never double-counted? How did you implement percentile ranking?*

> [Write your answer here]

---

### 4. Testing & Edge Cases
*What tests did you run, and what new unit test cases did you add to `tests/test_metrics_aggregator.py` (e.g. sub-second timestamps, empty datasets, large uniform distributions, multi-metric isolation)?*

> [Write your answer here]

---

### 5. Verification Method & Defect Prevention
*How did you verify that existing aggregations for full windows and non-boundary timestamps remain unaffected?*

> [Write your answer here]

---

### 6. AI Usage Disclosure
*Did you use AI coding assistants or LLM tools (e.g., Copilot, ChatGPT, Claude) during this challenge? If yes, describe how you used them and how you verified their suggestions. If no, state "None".*

> [Write your answer here]

---

### 7. Unresolved Items & Assumptions
*Are there any edge cases, assumptions, or future improvements (e.g. sliding vs tumbling windows, t-digest percentile approximations) that you feel warrant further discussion with the engineering team?*

> [Write your answer here]
