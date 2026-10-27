from dataclasses import dataclass
from typing import Optional


@dataclass
class RateLimitConfig:
    limit: int               # Maximum allowed requests per window
    window_seconds: float    # Window duration in seconds (e.g. 60.0)


@dataclass
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    retry_after: Optional[float] = None
    reset_in: float = 0.0


@dataclass
class ClientRequest:
    client_id: str
    endpoint: str
    timestamp: float
