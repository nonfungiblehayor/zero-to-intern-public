"""
AuthShield In-Memory Session and Token Store.
"""
from typing import Dict, List, Optional

try:
    from .models import Session, Token
except ImportError:
    from models import Session, Token


class SessionStore:
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._tokens: Dict[str, Token] = {}

    def save_session(self, session: Session) -> None:
        self._sessions[session.session_id] = session

    def get_session(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def revoke_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if session:
            session.is_revoked = True
            return True
        return False

    def revoke_user_sessions(self, user_id: str) -> int:
        count = 0
        for session in self._sessions.values():
            if session.user_id == user_id and not session.is_revoked:
                session.is_revoked = True
                count += 1
        return count

    def save_token(self, token: Token) -> None:
        self._tokens[token.token_id] = token

    def get_token(self, token_id: str) -> Optional[Token]:
        return self._tokens.get(token_id)

    def mark_token_used(self, token_id: str) -> bool:
        token = self._tokens.get(token_id)
        if token:
            token.is_used = True
            return True
        return False

    def get_tokens_for_session(self, session_id: str) -> List[Token]:
        return [t for t in self._tokens.values() if t.session_id == session_id]

    def clear(self) -> None:
        self._sessions.clear()
        self._tokens.clear()
