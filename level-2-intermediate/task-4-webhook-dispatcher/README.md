# Candidate Brief: EventBridge Webhook Dispatcher
**Assessment ID:** `BH-L2-004`  
**[CANDIDATE MATERIAL]**

---

## Welcome to the Team

Welcome to the Event Systems engineering team at **EventBridge**. We operate the asynchronous webhook delivery pipeline responsible for signing event payloads and dispatching them with reliable exponential backoff to thousands of customer endpoints.

Our modular architecture coordinates webhook deliveries across layers:
- `models.py`: Domain dataclasses (`WebhookEndpoint`, `WebhookEvent`, `DeliveryAttempt`, `DeliveryRecord`, `DeliveryStatus`).
- `signer.py`: Cryptographic HMAC-SHA256 signature generator.
- `retry_policy.py`: Retry eligibility and exponential backoff calculator.
- `dispatcher.py`: Delivery orchestrator coordinating signing, HTTP execution, and status transitions.

Recently, our Developer Platform and Customer Engineering teams escalated three critical production tickets:
- **Ticket #HOOK-401 (HMAC Signature Mismatch):** Major enterprise customers report that webhook signature verification consistently fails with `InvalidSignatureError`. Customers cannot verify whether requests originate from EventBridge.
- **Ticket #HOOK-402 (Client 4xx Infinite Retry Storm):** When a partner server responds with `401 Unauthorized` or `404 Not Found` (due to disabled webhook URLs or rotated keys), our dispatcher retries the request until `max_attempts` is exhausted, generating thousands of useless error logs.
- **Ticket #HOOK-403 (Linear Rather than Exponential Backoff):** Delivery attempts on failed endpoints retry at flat 2.0-second intervals rather than backing off exponentially ($1\text{s} \to 2\text{s} \to 4\text{s}$).

You are tasked with investigating where cryptographic and protocol logic broke down, implementing an architecturally sound solution, and protecting our webhook pipeline against regressions.

---

## 🚀 Running the Fullstack Application & Tests

This task is configured as a **Fullstack Application (API + React UI)** with unit tests. You can test your changes using either the interactive web console or the automated test suite.

### Option A: Interactive Webhook Studio (Web UI)
1. **Launch the Backend API Server:**
   ```bash
   python3 api.py
   ```
   *Runs on `http://localhost:8000` (FastAPI / Swagger docs at `/docs` if requirements installed, with built-in HTTP fallback).*

2. **Launch the Frontend Console:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   *Open `http://localhost:5173` in your browser.*
   - Test live webhook dispatches with customizable payloads.
   - Use the **1-Click Defect Reproduction Suite** to observe signature mismatches and 4xx retry storms in real time before and after your fix.

### Option B: Command-Line Test Suite
Run the test suite directly from the task root:
```bash
python3 -m unittest discover tests
```
Observe failures in:
- `test_bug_reproduction_ticket_hook_401_canonical_json_hmac`
- `test_bug_reproduction_ticket_hook_402_client_4xx_should_not_retry`
- `test_bug_reproduction_ticket_hook_403_exponential_backoff_progression`

---

## Your Objectives

1. **Investigate Codebase:**
   - Explore `src/`:
     - `models.py`: Domain dataclasses.
     - `signer.py`: Cryptographic HMAC-SHA256 signature generator (**YOUR TASK IS HERE**).
     - `retry_policy.py`: Retry eligibility and exponential backoff calculator (**YOUR TASK IS HERE**).
     - `dispatcher.py`: Delivery orchestrator coordinating signing and dispatch.

2. **Analyze Root Causes:**
   - **Canonical Serialization:** Why does `str(payload)` produce invalid signatures on customer receivers compared to canonical JSON?
   - **HTTP Status Discrimination:** Why is retrying 401 Unauthorized or 404 Not Found harmful to downstream systems and contrary to webhook standards?
   - **Backoff Math:** What formula generates exponential intervals across attempts?

3. **Implement the Fix:**
   - In `src/signer.py`:
     - Validate that `secret` is a non-empty string; raise `ValueError` otherwise.
     - Ensure payload is serialized to canonical JSON format: `json.dumps(payload, sort_keys=True, separators=(',', ':'))` before signing.
   - In `src/retry_policy.py`:
     - Validate constructor parameters (`max_attempts >= 1`, `initial_delay > 0`, `backoff_factor >= 1.0`).
     - `is_retryable`: Only retry when `status_code is None` (network timeout) or $500 \le \text{status\_code} < 600$ (server error). Do NOT retry 4xx client errors.
     - `compute_next_delay`: Use formula `initial_delay * (backoff_factor ** (attempt_count - 1))`.

4. **Expand Test Coverage:**
   - Add unit tests in `tests/test_webhook_dispatcher.py` covering:
     - 5xx server error retries.
     - Network timeouts.
     - Inactive endpoint rejection.
     - Maximum attempt exhaustion.

5. **Prepare for Technical Defense:**
   - Be prepared to discuss idempotent webhook delivery, dead-letter queues (DLQs), and HMAC signing best practices during your technical interview.

---

## Rules and Guidelines

- Python 3 Standard Library only (`hmac`, `hashlib`, `json`, `dataclasses`).
- Do not alter public method signatures or dataclass definitions.
- Demonstrate clean engineering practices and regression prevention.
