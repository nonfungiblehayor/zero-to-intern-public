# Candidate Submission Form: Bug Hunt BH-L2-003
**[CANDIDATE MATERIAL]**

Please complete this form before submitting your assessment. Be concise, precise, and technical.

---

### Candidate Information
- **Candidate Name:**
- **Submission Date:**
- **Time Spent (minutes):**

---

### 1. Root-Cause Analysis
*What was the root cause of the bugs reported in Tickets #AUTH-301, #AUTH-302, and #AUTH-303? Trace how session state is checked across `TokenService` and `AuthMiddleware`.*

> [Write your answer here]

---

### 2. Implementation Summary
*What specific changes did you make in `src/token_service.py` to fix session revocation, enforce refresh token rotation, and handle expiration boundaries?*

> [Write your answer here]

---

### 3. Solution Justification & Security Architecture
*Why is verifying session revocation essential for stateful authentication architectures? How does your refresh token rotation prevent replay attacks?*

> [Write your answer here]

---

### 4. Testing & Edge Cases
*What tests did you run, and what new unit test cases did you add to `tests/test_session_manager.py` (e.g. bulk user session revocation, expired refresh tokens, malformed headers, tampering)?*

> [Write your answer here]

---

### 5. Verification Method & Defect Prevention
*How did you verify that your changes did not break valid user logins, ongoing active sessions, or normal token refresh cycles?*

> [Write your answer here]

---

### 6. AI Usage Disclosure
*Did you use AI coding assistants or LLM tools (e.g., Copilot, ChatGPT, Claude) during this challenge? If yes, describe how you used them and how you verified their suggestions. If no, state "None".*

> [Write your answer here]

---

### 7. Unresolved Items & Assumptions
*Are there any edge cases, assumptions, or future improvements (e.g. distributed Redis session stores, sliding session expiration) that you feel warrant further discussion with the engineering team?*

> [Write your answer here]
