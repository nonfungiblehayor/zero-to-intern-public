"""
Unit tests for AuthShield Session & Token Management.
"""
import unittest
from datetime import datetime, timedelta
import os
import sys

# Ensure src is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from models import TokenType
from session_store import SessionStore
from token_service import TokenService
from auth_middleware import AuthMiddleware


class TestSessionManager(unittest.TestCase):
    def setUp(self):
        self.store = SessionStore()
        self.service = TokenService(self.store)
        self.middleware = AuthMiddleware(self.service)
        self.base_time = datetime(2026, 10, 27, 12, 0, 0)

    def test_basic_login_and_authenticate(self):
        """A valid user creates a session, gets tokens, and authenticates successfully."""
        session = self.service.create_session("user_42", current_time=self.base_time)
        access_tok, refresh_tok = self.service.issue_tokens(session.session_id, current_time=self.base_time)

        status, headers, body = self.middleware.authenticate_request(
            {"Authorization": f"Bearer {access_tok.token_id}"},
            current_time=self.base_time + timedelta(minutes=5),
        )
        self.assertEqual(status, 200)
        self.assertEqual(body, "user_42")

    def test_bug_reproduction_ticket_auth_301_revocation_bypass(self):
        """
        REPRODUCTION TEST 1 (Ticket #AUTH-301):
        When a session is revoked (user logs out or admin revokes session),
        unexpired access tokens associated with that session must be rejected.
        """
        session = self.service.create_session("user_42", current_time=self.base_time)
        access_tok, _ = self.service.issue_tokens(session.session_id, current_time=self.base_time)

        # User logs out 2 minutes later
        self.store.revoke_session(session.session_id)

        # Attempt to access resource 3 minutes later
        result = self.service.validate_access_token(
            access_tok.token_id,
            current_time=self.base_time + timedelta(minutes=3),
        )
        self.assertFalse(
            result.is_valid,
            "Security vulnerability: Access token remained valid after session was revoked!"
        )
        self.assertEqual(result.error_code, "SESSION_REVOKED")

    def test_bug_reproduction_ticket_auth_302_refresh_token_reuse(self):
        """
        REPRODUCTION TEST 2 (Ticket #AUTH-302):
        Refresh token rotation requires that an already used refresh token
        cannot be reused to generate new tokens.
        """
        session = self.service.create_session("user_99", current_time=self.base_time)
        _, refresh_tok = self.service.issue_tokens(session.session_id, current_time=self.base_time)

        # Legitimate client refreshes token
        new_acc_1, new_ref_1 = self.service.refresh_token(
            refresh_tok.token_id,
            current_time=self.base_time + timedelta(minutes=10),
        )
        self.assertIsNotNone(new_acc_1)

        # Attacker tries to reuse old refresh token
        with self.assertRaises(ValueError, msg="Old refresh token was reused! Missing token rotation enforcement."):
            self.service.refresh_token(
                refresh_tok.token_id,
                current_time=self.base_time + timedelta(minutes=11),
            )

    def test_bug_reproduction_ticket_auth_303_exact_expiration_boundary(self):
        """
        REPRODUCTION TEST 3 (Ticket #AUTH-303):
        A token whose expiration timestamp is equal to the current time
        is expired and must not be accepted.
        """
        session = self.service.create_session("user_10", current_time=self.base_time)
        access_tok, _ = self.service.issue_tokens(session.session_id, current_time=self.base_time)

        # Check at exact expiration time (15 minutes exactly)
        exact_exp_time = self.base_time + timedelta(minutes=15)
        result = self.service.validate_access_token(
            access_tok.token_id,
            current_time=exact_exp_time,
        )
        self.assertFalse(
            result.is_valid,
            "Boundary error: Token evaluated as valid at exact expiration timestamp!"
        )
        self.assertEqual(result.error_code, "TOKEN_EXPIRED")


if __name__ == "__main__":
    unittest.main()
