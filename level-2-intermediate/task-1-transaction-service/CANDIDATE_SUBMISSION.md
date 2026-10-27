# Candidate Submission Form: Bug Hunt BH-L2-001
**[CANDIDATE MATERIAL]**

Please complete this form before submitting your assessment. Be concise, precise, and technical.

---

### Candidate Information
- **Candidate Name:**
- **Submission Date:**
- **Time Spent (minutes):**

---

### 1. Root-Cause Analysis
*What was the root cause of the bugs reported in Tickets #FIN-201 and #FIN-202? Explain how the interaction between the repository query, service layer, and summary calculator allowed non-completed transactions to pollute customer account summaries.*

> [Write your answer here]

---

### 2. Implementation Summary
*What specific architectural changes did you make across the modules (`src/service.py`, `src/calculator.py`, or `src/repository.py`)? Summarize where and how status filtering is now enforced.*

> [Write your answer here]

---

### 3. Solution Justification & Component Boundaries
*Why did you choose your specific layer to enforce transaction eligibility? How does your solution maintain clean separation of concerns without breaking existing queries?*

> [Write your answer here]

---

### 4. Testing & Edge Cases
*What tests did you run, and what new test cases did you add to `tests/test_summary_service.py` (e.g. date boundaries, mixed debit/credit statuses, large volume, empty accounts)?*

> [Write your answer here]

---

### 5. Verification Method & Regression Prevention
*How did you verify that your changes did not break accounts with only completed transactions or empty accounts?*

> [Write your answer here]

---

### 6. AI Usage Disclosure
*Did you use AI coding assistants or LLM tools (e.g., Copilot, ChatGPT, Claude) during this challenge? If yes, describe how you used them and how you verified their suggestions. If no, state "None".*

> [Write your answer here]

---

### 7. Unresolved Items & Assumptions
*Are there any edge cases, assumptions, or future improvements that you feel remain unresolved or would warrant further discussion with the engineering team?*

> [Write your answer here]
