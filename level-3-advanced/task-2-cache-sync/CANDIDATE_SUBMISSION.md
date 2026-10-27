# Candidate Submission Form: Bug Hunt BH-L3-002
**[CANDIDATE MATERIAL]**

Please complete this form before submitting your assessment. Be concise, precise, and technical.

---

### Candidate Information
- **Candidate Name:**
- **Submission Date:**
- **Time Spent (minutes):**

---

### 1. Root-Cause Analysis
*What was the root cause of the bugs reported in Tickets #CACHE-601, #CACHE-602, and #CACHE-603? Trace how dirty buffer prioritization, eviction handling, and TTL expiration interact.*

> [Write your answer here]

---

### 2. Implementation Summary
*What specific changes did you make in `src/cache_manager.py` to restore read-your-own-writes consistency, protect dirty writes across eviction, and enforce TTL bounds?*

> [Write your answer here]

---

### 3. Solution Justification & Memory Management
*How does your corrected architecture prevent silent data loss during aggressive cache eviction? How do you ensure expired keys are cleaned from memory?*

> [Write your answer here]

---

### 4. Testing & Edge Cases
*What tests did you run, and what new unit test cases did you add to `tests/test_cache_sync.py` (e.g. concurrent buffer flush, TTL expiration on dirty keys, zero-capacity caches, repeated overwrites)?*

> [Write your answer here]

---

### 5. Verification Method & Defect Prevention
*How did you verify that cache hit rates, write buffer flushes, and backing store operations function correctly?*

> [Write your answer here]

---

### 6. AI Usage Disclosure
*Did you use AI coding assistants or LLM tools (e.g., Copilot, ChatGPT, Claude) during this challenge? If yes, describe how you used them and how you verified their suggestions. If no, state "None".*

> [Write your answer here]

---

### 7. Unresolved Items & Assumptions
*Are there any edge cases, assumptions, or future improvements (e.g. write-behind persistence, asynchronous thread safety, distributed invalidation) that you feel warrant further discussion with the engineering team?*

> [Write your answer here]
