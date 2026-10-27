"""
AuthShield Session & Token Domain Models.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class TokenType(Enum):
    ACCESS = "ACCESS"
    REFRESH = "REFRESH"


@dataclass
class Session:
    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    is_revoked: bool = False


@dataclass
class Token:
    token_id: str
    session_id: str
    user_id: str
    token_type: TokenType
    created_at: datetime
    expires_at: datetime
    is_used: bool = False


@dataclass
class TokenValidationResult:
    is_valid: bool
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
