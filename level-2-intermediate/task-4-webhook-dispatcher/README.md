# Candidate Brief: EventBridge Webhook Dispatcher
**Assessment ID:** `BH-L2-004`  
**[CANDIDATE MATERIAL]**

---

## Welcome to EventBridge

Welcome to the Event Systems engineering team at **EventBridge**. We operate the asynchronous webhook delivery pipeline responsible for signing event payloads and dispatching them with reliable exponential backoff to thousands of customer endpoints.

Recently, our Developer Platform and Customer Engineering teams escalated three critical production tickets:
- **Ticket #HOOK-401 (HMAC Signature Mismatch):** Major enterprise customers report that webhook signature verification consistently fails with `InvalidSignatureError`. Customers cannot verify whether requests originate from EventBridge.
- **Ticket #HOOK-402 (Client 4xx Infinite Retry Storm):** When a partner server responds with `401 Unauthorized` or `404 Not Found` (due to disabled webhook URLs or rotated keys), our dispatcher retries the request until `max_attempts` is exhausted, generating thousands of useless error logs.
- **Ticket #HOOK-403 (Linear Rather than Exponential Backoff):** Delivery attempts on failed endpoints retry at flat 2.0-second intervals rather than backing off exponentially ($1\text{s} \to 2\text{s} \to 4\text{s}$).

You are tasked with investigating where cryptographic and protocol logic broke down, implementing an architecturally sound solution, and protecting our webhook pipeline against regressions.

---

## Your Objectives

1. **Investigate Codebase:**
   - `src/models.py`: Domain dataclasses (`WebhookEndpoint`, `WebhookEvent`, `DeliveryAttempt`, `DeliveryRecord`, `DeliveryStatus`).
   - `src/signer.py`: Cryptographic HMAC-SHA256 signature generator.
   - `src/retry_policy.py`: Retry eligibility and exponential backoff calculator.
   - `src/dispatcher.py`: Delivery orchestrator coordinating signing, HTTP execution, and status transitions.
2. **Reproduce the Defect:**
   ```bash
   python3 -m unittest discover tests
   ```
   Observe the failures in:
   - `test_bug_reproduction_ticket_hook_401_canonical_json_hmac`
   - `test_bug_reproduction_ticket_hook_402_client_4xx_should_not_retry`
   - `test_bug_reproduction_ticket_hook_403_exponential_backoff_progression`
3. **Analyze Root Causes:**
   - **Canonical Serialization:** Why does `str(payload)` produce invalid signatures on customer receivers?
   - **HTTP Status Discrimination:** Why is retrying 401 Unauthorized or 404 Not Found harmful to downstream systems?
   - **Backoff Math:** What formula generates exponential intervals across attempts?
4. **Implement the Fix:**
   - In `src/signer.py`:
     - Ensure payload is serialized to canonical JSON format: `json.dumps(payload, sort_keys=True, separators=(',', ':'))` before signing.
   - In `src/retry_policy.py`:
     - `is_retryable`: Only retry when `status_code is None` (network timeout) or $500 \le \text{status\_code} < 600$ (server error). Do NOT retry 4xx client errors.
     - `compute_next_delay`: Use formula `initial_delay * (backoff_factor ** (attempt_count - 1))`.
5. **Add Unit Tests:**
   - Expand `tests/test_webhook_dispatcher.py` to cover server errors (500), network timeouts, max attempt exhaustion, and inactive endpoints.
6. **Complete Documentation:**
   - Fill out all sections in [CANDIDATE_SUBMISSION.md](file:///home/l2e/Documents/talent-nation/zero-to-intern/Bug-Hunt/level-2-intermediate/task-4-webhook-dispatcher/starter_repo/CANDIDATE_SUBMISSION.md).

---

## Rules and Guidelines

- Python 3 Standard Library only. Do not install external libraries.
- Do not alter public method signatures or dataclass definitions.
- Document all security and protocol trade-offs in `CANDIDATE_SUBMISSION.md`.
