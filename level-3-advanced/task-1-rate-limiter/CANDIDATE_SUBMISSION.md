# Candidate Submission Form: Bug Hunt BH-L3-001
**[CANDIDATE MATERIAL]**

Please complete this form before submitting your assessment. Be concise, precise, and technical.

---

### Candidate Information
- **Candidate Name:**
- **Submission Date:**
- **Time Spent (minutes):**

---

### 1. Root-Cause Analysis
*What was the root cause of the bugs reported in Tickets #GATE-401, #GATE-402, and #GATE-403? Explain mathematically why the sliding window weighting was inverted, and why dormant clients had their traffic resurrected after hours of inactivity.*

> [Write your answer here]

---

### 2. Implementation Summary
*What specific code changes did you make in `src/limiter.py` and `src/gateway.py` to correct the sliding window algorithm and header calculations?*

> [Write your answer here]

---

### 3. Solution Justification & Algorithm Verification
*How does your corrected formula mathematically reflect traffic decay over sliding windows? How did you verify that inactive clients are properly handled across multiple window periods?*

> [Write your answer here]

---

### 4. Testing & Edge Cases
*What tests did you run, and what new test cases did you add to `tests/test_rate_limiter.py` (e.g. boundary conditions, sub-second precision, multi-client concurrency simulation, exact rate limit saturation)?*

> [Write your answer here]

---

### 5. Verification Method & Edge Architecture
*How did you verify that the HTTP header contract (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `Retry-After`) conforms strictly to standard API gateway specifications?*

> [Write your answer here]

---

### 6. AI Usage Disclosure
*Did you use AI coding assistants or LLM tools (e.g., Copilot, ChatGPT, Claude) during this challenge? If yes, describe how you used them and how you verified their suggestions. If no, state "None".*

> [Write your answer here]

---

### 7. Unresolved Items & Assumptions
*Are there any edge cases, assumptions, or future improvements (e.g. distributed Redis storage, race condition locking) that you feel remain unresolved or would warrant further discussion with the engineering team?*

> [Write your answer here]
