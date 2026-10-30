# Candidate Brief: CloudGate Sliding-Window Rate Limiter
**Assessment ID:** `BH-L3-001`  
**[CANDIDATE MATERIAL]**

---

## Welcome to CloudGate

Welcome to the Infrastructure & Traffic Management engineering team at **CloudGate**. We operate the edge API gateway that fronts mission-critical microservices for enterprise customers.

Our gateway implements a **Sliding-Window Counter Rate Limiter** to protect downstream services against traffic spikes and denial-of-service attempts while granting clients smooth, fair throughput across rolling time windows.

Recently, our Site Reliability Engineers (SREs) and Customer Success team escalated three high-severity production tickets:
- **Ticket #GATE-401 (Spurious Mid-Window Throttling):** Enterprise API partners report unexpected HTTP 429 (`Too Many Requests`) errors when sending steady, compliant traffic. Telemetry reveals that as time progresses further into the rate limit window, the algorithm incorrectly over-penalizes clients rather than granting more capacity as old traffic expires.
- **Ticket #GATE-402 (Idle Client Traffic Resurrection):** An automated background job that runs once per hour sends 10 requests at 01:00. When it awakens at 02:00, its very first request is immediately rejected with HTTP 429, despite having sent zero requests for 59 minutes!
- **Ticket #GATE-403 (Negative Rate-Limit Headers):** Enterprise SDKs are throwing parse exceptions on responses containing `X-RateLimit-Remaining: -1`. The RFC and API contract require this header to represent remaining available quota, clamped at a minimum of `0`.

You are tasked with diagnosing the algorithmic defects across our gateway codebase, implementing an architecturally sound solution, verifying behavior deterministically using our test clock, and preparing to defend your architecture in your technical interview.

---

## 🚀 Running the Fullstack Application & Tests

This task is configured as a **Fullstack Application (API + React UI)** with unit tests. You can test your changes using either the interactive web console or the automated test suite.

### Option A: Interactive Gateway Studio (Web UI)
1. **Launch the Backend API Server:**
   ```bash
   python3 api.py
   ```
   *Runs on `http://localhost:8000` (FastAPI / Swagger docs at `/docs` if requirements installed, with built-in zero-dependency fallback).*

2. **Launch the Frontend Console:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   *Open `http://localhost:5173` in your browser.*
   - Test live gateway requests and dispatch bursts.
   - Use the **Virtual Time Machine** to advance clock time deterministically without sleeping.
   - Use the **1-Click Defect Reproduction Suite** to observe inverted sliding weight, dormant traffic resurrection, and negative header underflow in real time before and after your fix.

### Option B: Command-Line Test Suite
Run the test suite directly from the task root:
```bash
python3 -m unittest discover tests
```
Observe failures in:
- `test_bug_reproduction_ticket_gate_401_sliding_weight`
- `test_bug_reproduction_ticket_gate_402_idle_resurrection`
- `test_bug_reproduction_ticket_gate_403_remaining_header_zero`

---

## Your Objectives

1. **Investigate the Codebase Architecture:**
   - Explore `src/`:
     - `models.py`: Data entities (`RateLimitConfig`, `RateLimitResult`, `ClientRequest`).
     - `clock.py`: Time provider interface (`Clock` and `TestClock`).
     - `storage.py`: In-memory state store (`SlidingWindowStore`, `ClientWindowData`).
     - `limiter.py`: Core mathematical rate limiting algorithm (`SlidingWindowRateLimiter`, **YOUR TASK IS HERE**).
     - `gateway.py`: Gateway interface (`APIGateway`) translating rate limit decisions to HTTP statuses and response headers.

2. **Analyze Root Causes:**
   - **Sliding-Window Math:** Look at how `weight` is computed in `limiter.py`. As `time_into_current` approaches `window_duration`, what should happen to the weight of the previous window?
   - **Window Advancement Across Gaps:** When a client is idle for multiple window lengths ($> 2 \times \text{window\_duration}$), what should happen to `previous_window_count` and `current_window_count`?
   - **Header Sanitization:** When a request is rejected ($429$), what value must `X-RateLimit-Remaining` contain?

3. **Implement the Fix:**
   - In `src/limiter.py`:
     - Correct the weight calculation:
       $$\text{weight} = \max\left(0.0, \min\left(1.0, 1.0 - \frac{\text{time\_into\_current}}{\text{window\_duration}}\right)\right)$$
     - Correct window advancement:
       - If the elapsed time since current window start is $\ge 2 \times \text{window\_duration}$, both `previous_count` and `current_count` must be reset to `0`, and `current_window_start = now`.
       - If elapsed time is $\ge 1 \times \text{window\_duration}$ (and $< 2 \times \text{window\_duration}$), shift `previous_count = current_count`, `current_count = 0`, and advance `current_window_start += window_duration`.
     - Clamp remaining requests:
       $$\text{remaining} = \max(0, \text{limit} - \text{estimated\_count} - 1) \quad (\text{if allowed})$$
       $$\text{remaining} = 0 \quad (\text{if rejected})$$

4. **Expand Test Coverage:**
   - Add unit tests in `tests/test_rate_limiter.py` covering:
     - Multi-client isolation (traffic on client A does not affect client B).
     - Sub-second sliding windows (e.g., 100 requests per 0.5 seconds).
     - Rapid consecutive requests within the same millisecond.
     - Input validation (empty or non-string client IDs).

5. **Prepare for Technical Defense:**
   - Be prepared to discuss rate limiting algorithms (token bucket, leaky bucket, fixed window, sliding window counter), distributed Redis storage challenges, and clock skew mitigation during your technical interview.

---

## Rules and Guidelines

- Python 3 Standard Library only.
- Do not use `time.sleep()` in test cases. Use the provided `TestClock` to advance time deterministically.
- Do not alter public interfaces of `RateLimitConfig`, `RateLimitResult`, `Clock`, or `APIGateway.handle_request`.
