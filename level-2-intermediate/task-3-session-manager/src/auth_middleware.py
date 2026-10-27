"""
AuthShield HTTP Authorization Header Middleware.
"""
from typing import Dict, Optional, Tuple

try:
    from .token_service import TokenService
except ImportError:
    from token_service import TokenService


class AuthMiddleware:
    def __init__(self, token_service: TokenService):
        self.token_service = token_service

    def authenticate_request(
        self,
        headers: Dict[str, str],
        current_time=None,
    ) -> Tuple[int, Dict[str, str], Optional[str]]:
        """
        Extracts Bearer token from Authorization header and validates it.
        Returns: (http_status, response_headers, user_id_or_error)
        """
        auth_header = headers.get("Authorization") or headers.get("authorization")
        if not auth_header:
            return 401, {"WWW-Authenticate": "Bearer"}, "Missing Authorization header"

        parts = auth_header.strip().split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return 401, {"WWW-Authenticate": "Bearer"}, "Invalid Authorization header format"

        token_id = parts[1].strip()
        result = self.token_service.validate_access_token(token_id, current_time=current_time)

        if not result.is_valid:
            return 401, {"WWW-Authenticate": f'Bearer error="{result.error_code}"'}, result.error_message or "Unauthorized"

        return 200, {"X-Authenticated-User": result.user_id}, result.user_id
