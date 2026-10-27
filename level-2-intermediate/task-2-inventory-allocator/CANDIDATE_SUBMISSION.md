# Candidate Submission Form: Bug Hunt BH-L2-002
**[CANDIDATE MATERIAL]**

Please complete this form before submitting your assessment. Be concise, precise, and technical.

---

### Candidate Information
- **Candidate Name:**
- **Submission Date:**
- **Time Spent (minutes):**

---

### 1. Root-Cause Analysis
*What was the root cause of the bugs reported in Tickets #SHIP-301 and #SHIP-302? Explain how partial failures during order allocation caused inventory state corruption (zombie reservations).*

> [Write your answer here]

---

### 2. Implementation Summary
*What specific code changes did you make in `src/allocation_service.py` to ensure transactional rollback across all regional warehouses?*

> [Write your answer here]

---

### 3. Solution Justification & Error Handling
*How does your rollback logic handle multiple warehouses and diverse exception types? Why does it guarantee that inventory is never leaked?*

> [Write your answer here]

---

### 4. Testing & Edge Cases
*What tests did you run, and what new test cases did you add to `tests/test_allocation_service.py` (e.g. 3+ warehouses, exact stock depletion, partial matches, duplicate SKUs)?*

> [Write your answer here]

---

### 5. Verification Method & Regression Prevention
*How did you verify that successful full allocations remain completely unaffected by your rollback logic?*

> [Write your answer here]

---

### 6. AI Usage Disclosure
*Did you use AI coding assistants or LLM tools (e.g., Copilot, ChatGPT, Claude) during this challenge? If yes, describe how you used them and how you verified their suggestions. If no, state "None".*

> [Write your answer here]

---

### 7. Unresolved Items & Assumptions
*Are there any edge cases, assumptions, or future improvements (e.g. concurrent order locking) that you feel remain unresolved or would warrant further discussion with the engineering team?*

> [Write your answer here]
