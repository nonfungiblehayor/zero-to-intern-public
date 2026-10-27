from typing import Dict, Any, Tuple
from models import ClientRequest, RateLimitConfig, RateLimitResult
from limiter import SlidingWindowRateLimiter


class APIGateway:
    """API Gateway edge proxy enforcing rate limits and HTTP header injection."""

    def __init__(self, limiter: SlidingWindowRateLimiter):
        self.limiter = limiter

    def handle_request(self, request: ClientRequest) -> Tuple[int, Dict[str, str], Dict[str, Any]]:
        if not request.client_id or not isinstance(request.client_id, str):
            raise ValueError("client_id must be a non-empty string.")

        result: RateLimitResult = self.limiter.check(request.client_id)

        headers = {
            "X-RateLimit-Limit": str(result.limit),
            "X-RateLimit-Remaining": str(result.remaining),
            "X-RateLimit-Reset": str(result.reset_in),
        }

        if result.allowed:
            return 200, headers, {"status": "success", "endpoint": request.endpoint}
        else:
            headers["Retry-After"] = str(result.retry_after)
            return 429, headers, {
                "status": "error",
                "message": "Too Many Requests",
                "retry_after": result.retry_after
            }
