# Candidate Submission Form: Bug Hunt BH-L2-004
**[CANDIDATE MATERIAL]**

Please complete this form before submitting your assessment. Be concise, precise, and technical.

---

### Candidate Information
- **Candidate Name:**
- **Submission Date:**
- **Time Spent (minutes):**

---

### 1. Root-Cause Analysis
*What was the root cause of the bugs reported in Tickets #HOOK-401, #HOOK-402, and #HOOK-403? Trace how payload serialization affects HMAC cryptographic signatures and why client 4xx status codes should not be retried.*

> [Write your answer here]

---

### 2. Implementation Summary
*What specific changes did you make in `src/signer.py` and `src/retry_policy.py` to fix canonical JSON signing, exponential backoff, and non-retryable status codes?*

> [Write your answer here]

---

### 3. Solution Justification & Protocol Security
*Why is canonical JSON serialization (key ordering, whitespace suppression) critical for webhook cryptographic signatures? How does distinguishing between 4xx and 5xx status codes protect distributed systems?*

> [Write your answer here]

---

### 4. Testing & Edge Cases
*What tests did you run, and what new unit test cases did you add to `tests/test_webhook_dispatcher.py` (e.g. network timeout retries, max attempt exhaustion, inactive endpoint rejection, nested JSON payloads)?*

> [Write your answer here]

---

### 5. Verification Method & Defect Prevention
*How did you verify that successful 2xx deliveries still succeed without unintended side-effects?*

> [Write your answer here]

---

### 6. AI Usage Disclosure
*Did you use AI coding assistants or LLM tools (e.g., Copilot, ChatGPT, Claude) during this challenge? If yes, describe how you used them and how you verified their suggestions. If no, state "None".*

> [Write your answer here]

---

### 7. Unresolved Items & Assumptions
*Are there any edge cases, assumptions, or future improvements (e.g. dead-letter queues, jitter on exponential backoff) that you feel warrant further discussion with the engineering team?*

> [Write your answer here]
