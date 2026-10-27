# Candidate Submission Form: Bug Hunt BH-L1-003
**[CANDIDATE MATERIAL]**

Please complete this form before submitting your assessment. Be concise, precise, and technical.

---

### Candidate Information
- **Candidate Name:**
- **Submission Date:**
- **Time Spent (minutes):**

---

### 1. Root-Cause Analysis
*What were the root causes of the bugs reported in Tickets #STATION-101, #STATION-102, and #STATION-103? Explain why initializing `min_temp` and `max_temp` to `0.0` fails for certain input ranges, and why empty lists trigger crashes.*

> [Write your answer here]

---

### 2. Implementation Summary
*What specific code changes did you make in `src/temperature_analyzer.py`? Summarize how you resolved sentinel initialization and empty list handling.*

> [Write your answer here]

---

### 3. Solution Justification
*Why does your fix resolve the underlying defect rather than just masking the symptoms for specific test values?*

> [Write your answer here]

---

### 4. Testing & Edge Cases
*What tests did you run, and what new test cases did you add to `tests/test_temperature_analyzer.py` (e.g. single-reading lists, uniform readings, invalid non-numeric inputs, float rounding precision)?*

> [Write your answer here]

---

### 5. Verification Method
*How did you verify that your changes did not alter the return dictionary schema or break freezing alert behavior?*

> [Write your answer here]

---

### 6. AI Usage Disclosure
*Did you use AI coding assistants or LLM tools (e.g., Copilot, ChatGPT, Claude) during this challenge? If yes, describe how you used them and how you verified their suggestions. If no, state "None".*

> [Write your answer here]

---

### 7. Unresolved Items & Assumptions
*Are there any edge cases, assumptions, or future improvements that you feel remain unresolved or would warrant further discussion with the team?*

> [Write your answer here]
