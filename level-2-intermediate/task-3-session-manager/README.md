# Candidate Brief: AuthShield Token & Session Manager
**Assessment ID:** `BH-L2-003`  
**[CANDIDATE MATERIAL]**

---

## Welcome to AuthShield

Welcome to the Identity & Security Infrastructure engineering team at **AuthShield**. We maintain the authentication and session management services protecting thousands of customer endpoints.

Our architecture separates authentication into distinct modules:
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

## Your Objectives

1. **Investigate Codebase:**
   - Explore `src/`:
     - `models.py`: Domain dataclasses (`Session`, `Token`, `TokenType`, `TokenValidationResult`).
     - `session_store.py`: In-memory storage for sessions and tokens.
     - `token_service.py`: Token issuance, validation, and rotation service.
     - `auth_middleware.py`: HTTP Authorization header authentication gateway.
2. **Reproduce the Incidents:**
   - Execute the test suite:
     ```bash
     python3 -m unittest discover tests
     ```
   - Observe the failures in:
     - `test_bug_reproduction_ticket_auth_301_revocation_bypass`
     - `test_bug_reproduction_ticket_auth_302_refresh_token_reuse`
     - `test_bug_reproduction_ticket_auth_303_exact_expiration_boundary`
3. **Analyze Root Causes:**
   - **Cross-Layer State:** Why did `validate_access_token` ignore whether `session.is_revoked`?
   - **Token Rotation:** Why did `refresh_token` issue new tokens without checking if the previous token was already used?
   - **Boundary Comparisons:** Why did using `<` instead of `<=` allow expired tokens to slip through?
4. **Implement the Fix in `src/token_service.py`:**
   - In `validate_access_token`:
     - Cross-check `self.store.get_session(token.session_id)`. If the session is missing or `session.is_revoked`, reject with `is_valid=False` and `error_code="SESSION_REVOKED"`.
     - Check session expiration (`session.expires_at <= now`).
     - Ensure expiration check uses `<= now` so tokens at exact expiration second are rejected.
   - In `refresh_token`:
     - Reject if `old_token.is_used` with a `ValueError("Refresh token has already been used")`.
     - Mark `old_token` as used: `self.store.mark_token_used(old_refresh_token_id)`.
5. **Expand Test Coverage:**
   - Add unit tests in `tests/test_session_manager.py` covering:
     - Multi-device user logout (`revoke_user_sessions`).
     - Expired refresh tokens.
     - Malformed or missing `Authorization` headers.
     - Input validation (empty user IDs).
6. **Submit Documentation:**
   - Complete all sections in [CANDIDATE_SUBMISSION.md](file:///home/l2e/Documents/talent-nation/zero-to-intern/Bug-Hunt/level-2-intermediate/task-3-session-manager/starter_repo/CANDIDATE_SUBMISSION.md).

---

## Rules and Guidelines

- Python 3 Standard Library only. Do not install external libraries.
- Do not alter public signatures or return types of `TokenService` methods.
- Document all security trade-offs in `CANDIDATE_SUBMISSION.md`.
