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

You are tasked with diagnosing the algorithmic defects across our gateway codebase, implementing an architecturally sound solution, verifying behavior deterministically using our test clock, and completing our engineering post-mortem.

---

## Your Objectives

1. **Investigate the Codebase Architecture:**
   - Explore `src/`:
     - `models.py`: Data entities (`RateLimitConfig`, `RateLimitResult`, `ClientWindowData`).
     - `clock.py`: Time provider interface (`Clock` and `SystemClock`).
     - `storage.py`: In-memory thread-safe state store (`InMemoryRateLimitStore`).
     - `limiter.py`: Core mathematical rate limiting algorithm (`SlidingWindowRateLimiter`).
     - `gateway.py`: Gateway interface (`ApiGateway`) translating rate limit decisions to HTTP statuses and response headers.
2. **Reproduce the Production Incidents:**
   - Execute the test suite:
     ```bash
     python3 -m unittest discover tests
     ```
   - Observe the failures in:
     - `test_bug_reproduction_ticket_gate_401_inverted_sliding_window_weight`
     - `test_bug_reproduction_ticket_gate_402_long_idle_interval_traffic_resurrection`
     - `test_bug_reproduction_ticket_gate_403_negative_remaining_header`
3. **Analyze Root Causes:**
   - **Sliding-Window Math:** Look at how `previous_weight` is computed in `limiter.py`. As `time_into_current` approaches `window_duration`, what should happen to the weight of the previous window?
   - **Window Advancement Across Gaps:** When a client is idle for multiple window lengths ($> 2 \times \text{window\_duration}$), what should happen to `previous_window_count` and `current_window_count`?
   - **Header Sanitization:** When a request is rejected ($429$), what value must `X-RateLimit-Remaining` contain?
4. **Implement the Fix:**
   - Correct the weight calculation:
     $$\text{previous\_weight} = \frac{\text{window\_duration} - \text{time\_into\_current}}{\text{window\_duration}}$$
   - Correct window advancement:
     - If the elapsed time since current window start is $\ge 2 \times \text{window\_duration}$, both `previous_count` and `current_count` must be reset to `0`, and `current_window_start` set to current time.
     - If elapsed time is $\ge 1 \times \text{window\_duration}$ (and $< 2 \times \text{window\_duration}$), shift `previous_count = current_count`, `current_count = 0`, and advance `current_window_start`.
   - Clamp remaining requests:
     $$\text{remaining} = \max(0, \text{limit} - \text{estimated\_count} - 1) \quad (\text{if allowed})$$
     $$\text{remaining} = 0 \quad (\text{if rejected})$$
5. **Expand Test Coverage:**
   - Add unit tests in `tests/test_rate_limiter.py` covering:
     - Multi-client isolation (traffic on client A does not affect client B).
     - Sub-second sliding windows (e.g. 100 requests per 0.5 seconds).
     - Rapid consecutive requests within the same millisecond.
     - Input validation (empty or non-string client IDs).
6. **Submit Your Technical Write-Up:**
   - Complete all sections in [CANDIDATE_SUBMISSION.md](file:///home/l2e/Documents/talent-nation/zero-to-intern/Bug-Hunt/level-3-advanced/task-1-rate-limiter/starter_repo/CANDIDATE_SUBMISSION.md).

---

## Rules and Guidelines

- Python 3 Standard Library only. Do not install external libraries.
- Do not use `time.sleep()` in test cases. Use the provided `TestClock` to advance time deterministically.
- Do not alter public interfaces of `RateLimitConfig`, `RateLimitResult`, `Clock`, or `ApiGateway.handle_request`.
