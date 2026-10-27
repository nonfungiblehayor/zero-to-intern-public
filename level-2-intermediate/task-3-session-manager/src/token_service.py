"""
AuthShield Token Generation, Validation, and Refresh Service.
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple

try:
    from .models import Session, Token, TokenType, TokenValidationResult
    from .session_store import SessionStore
except ImportError:
    from models import Session, Token, TokenType, TokenValidationResult
    from session_store import SessionStore


class TokenService:
    def __init__(self, store: Optional[SessionStore] = None):
        self.store = store if store is not None else SessionStore()

    def create_session(
        self,
        user_id: str,
        current_time: Optional[datetime] = None,
        duration: timedelta = timedelta(days=7),
    ) -> Session:
        now = current_time or datetime.utcnow()
        session = Session(
            session_id=f"sess_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            created_at=now,
            expires_at=now + duration,
            is_revoked=False,
        )
        self.store.save_session(session)
        return session

    def issue_tokens(
        self,
        session_id: str,
        current_time: Optional[datetime] = None,
    ) -> Tuple[Token, Token]:
        now = current_time or datetime.utcnow()
        session = self.store.get_session(session_id)
        if not session or session.is_revoked:
            raise ValueError(f"Session {session_id} does not exist or is revoked")

        access_token = Token(
            token_id=f"acc_{uuid.uuid4().hex}",
            session_id=session_id,
            user_id=session.user_id,
            token_type=TokenType.ACCESS,
            created_at=now,
            expires_at=now + timedelta(minutes=15),
            is_used=False,
        )
        refresh_token = Token(
            token_id=f"ref_{uuid.uuid4().hex}",
            session_id=session_id,
            user_id=session.user_id,
            token_type=TokenType.REFRESH,
            created_at=now,
            expires_at=now + timedelta(days=7),
            is_used=False,
        )

        self.store.save_token(access_token)
        self.store.save_token(refresh_token)
        return access_token, refresh_token

    def refresh_token(
        self,
        old_refresh_token_id: str,
        current_time: Optional[datetime] = None,
    ) -> Tuple[Token, Token]:
        now = current_time or datetime.utcnow()
        old_token = self.store.get_token(old_refresh_token_id)

        if not old_token:
            raise ValueError("Refresh token not found")
        if old_token.token_type != TokenType.REFRESH:
            raise ValueError("Token is not a refresh token")
        if old_token.expires_at <= now:
            raise ValueError("Refresh token expired")

        session = self.store.get_session(old_token.session_id)
        if not session or session.is_revoked:
            raise ValueError("Session is revoked or expired")

        # NOTE: Starter defect - does not check old_token.is_used, and does not mark old token as used!
        return self.issue_tokens(old_token.session_id, current_time=now)

    def validate_access_token(
        self,
        token_id: str,
        current_time: Optional[datetime] = None,
    ) -> TokenValidationResult:
        now = current_time or datetime.utcnow()
        token = self.store.get_token(token_id)

        if not token:
            return TokenValidationResult(
                is_valid=False,
                error_code="TOKEN_NOT_FOUND",
                error_message="Token was not found in registry",
            )

        if token.token_type != TokenType.ACCESS:
            return TokenValidationResult(
                is_valid=False,
                error_code="INVALID_TOKEN_TYPE",
                error_message="Expected access token",
            )

        # NOTE: Starter defect - uses < instead of <=, allowing token at exact expiration second
        if token.expires_at < now:
            return TokenValidationResult(
                is_valid=False,
                error_code="TOKEN_EXPIRED",
                error_message="Token has expired",
            )

        # NOTE: Starter defect - does NOT check session.is_revoked!

        return TokenValidationResult(
            is_valid=True,
            user_id=token.user_id,
            session_id=token.session_id,
        )
