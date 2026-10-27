"""
EventBridge Webhook Dispatcher Domain Models.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class DeliveryStatus(Enum):
    PENDING = "PENDING"
    DELIVERED = "DELIVERED"
    RETRYING = "RETRYING"
    FAILED = "FAILED"


@dataclass
class WebhookEndpoint:
    endpoint_id: str
    url: str
    secret: str
    is_active: bool = True


@dataclass
class WebhookEvent:
    event_id: str
    event_type: str
    payload: Dict[str, Any]
    timestamp: float


@dataclass
class DeliveryAttempt:
    attempt_number: int
    timestamp: float
    status_code: Optional[int]
    success: bool
    error: Optional[str] = None


@dataclass
class DeliveryRecord:
    event_id: str
    endpoint_id: str
    status: DeliveryStatus
    attempts: List[DeliveryAttempt] = field(default_factory=list)
    next_retry_at: Optional[float] = None
