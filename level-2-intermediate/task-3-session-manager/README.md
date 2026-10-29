# Candidate Brief: AuthShield Token & Session Manager
**Assessment ID:** `BH-L2-003`  
**[CANDIDATE MATERIAL]**

---

## Welcome to the Team

Welcome to the Identity & Security Infrastructure engineering team at **AuthShield**. We maintain the authentication, central session registry, and token management services protecting thousands of corporate customer endpoints.

Our modular architecture coordinates authentication across layers:
- `models.py`: Data entities representing sessions, tokens, and validation results.
- `session_store.py`: Central in-memory registry tracking session lifecycles and token states.
- `token_service.py`: Service issuing, validating, and rotating access and refresh tokens.
- `auth_middleware.py`: Gateway middleware parsing HTTP `Authorization` headers.

Recently, our Security Operations Center (SOC) escalated three urgent vulnerability tickets:
- **Ticket #AUTH-301 (Revocation Bypass):** When a user logs out, their session is marked as revoked in the database. However, active access tokens issued prior to logout remain accepted by the API gateway until their 15-minute expiration, creating an unauthorized access window.
- **Ticket #AUTH-302 (Refresh Token Reuse Vulnerability):** In our OAuth2/OIDC refresh flow, refresh tokens are supposed to rotate upon use. However, intercepted refresh tokens can be used repeatedly to generate infinite access tokens.
- **Ticket #AUTH-303 (Expiration Boundary Off-By-One):** Tokens examined at the exact second of expiration (`expires_at == now`) are treated as valid instead of expired.

You are tasked with investigating where cross-module validation broke down, implementing an architecturally sound solution, and protecting our authentication gateway against regressions.

---

## 🚀 Running the Fullstack Application & Tests

This task is configured as a **Fullstack Application (API + React UI)** with unit tests. You can test your changes using either the interactive web console or the automated test suite.

### Option A: Interactive SOC Console (Web UI)
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
   - Test live authentication requests against `/api/protected`.
   - Use the **1-Click Defect Reproduction Suite** to observe vulnerabilities in real time before and after your fix.

### Option B: Command-Line Test Suite
Run the test suite directly from the task root:
```bash
python3 -m unittest discover tests
```
Observe failures in:
- `test_bug_reproduction_ticket_auth_301_revocation_bypass`
- `test_bug_reproduction_ticket_auth_302_refresh_token_reuse`
- `test_bug_reproduction_ticket_auth_303_exact_expiration_boundary`

---

## Your Objectives

1. **Investigate Codebase:**
   - Explore `src/`:
     - `models.py`: Domain dataclasses (`Session`, `Token`, `TokenType`, `TokenValidationResult`).
     - `session_store.py`: In-memory storage for sessions and tokens.
     - `token_service.py`: Token issuance, validation, and rotation service (**YOUR TASK IS HERE**).
     - `auth_middleware.py`: HTTP Authorization header authentication gateway.

2. **Analyze Root Causes:**
   - **Cross-Layer State:** Why did `validate_access_token` ignore whether `session.is_revoked`?
   - **Token Rotation:** Why did `refresh_token` issue new tokens without checking if the previous token was already used or marking it spent?
   - **Boundary Comparisons:** Why did using `<` instead of `<=` allow expired tokens to slip through at the exact expiration second?

3. **Implement the Fix in `src/token_service.py`:**
   - In `create_session`:
     - Validate that `user_id` is a non-empty string; raise `ValueError` otherwise.
   - In `issue_tokens`:
     - Ensure the underlying session is not expired (`session.expires_at <= now`).
   - In `validate_access_token`:
     - Cross-check `self.store.get_session(token.session_id)`. If the session is missing or `session.is_revoked`, reject with `is_valid=False` and `error_code="SESSION_REVOKED"`.
     - Check session expiration (`session.expires_at <= now`).
     - Ensure expiration check uses `<= now` so tokens at exact expiration second are rejected.
   - In `refresh_token`:
     - Reject if `old_token.is_used` with `ValueError("Refresh token has already been used")`.
     - Mark `old_token` as used: `self.store.mark_token_used(old_refresh_token_id)`.

4. **Expand Test Coverage:**
   - Add unit tests in `tests/test_session_manager.py` covering:
     - Multi-device user logout (`revoke_user_sessions`).
     - Expired refresh tokens.
     - Malformed or missing `Authorization` headers.
     - Input validation (empty user IDs).

5. **Prepare for Technical Defense:**
   - Be prepared to discuss session revocation strategies (e.g. distributed blocklists vs token introspection), replay defense, and defense-in-depth during your technical interview.

---

## Rules and Guidelines

- Python 3 Standard Library only for backend logic (`dataclasses`, `enum`, `datetime`, `uuid`).
- Do not alter public signatures or return types of `TokenService` methods.
- Demonstrate clean engineering practices and regression prevention.
