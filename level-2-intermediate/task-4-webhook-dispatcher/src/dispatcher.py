"""
EventBridge Webhook Dispatcher Service.
"""
import json
from typing import Callable, Dict, List, Optional, Tuple, Any

try:
    from .models import WebhookEndpoint, WebhookEvent, DeliveryAttempt, DeliveryRecord, DeliveryStatus
    from .signer import WebhookSigner
    from .retry_policy import RetryPolicy
except ImportError:
    from models import WebhookEndpoint, WebhookEvent, DeliveryAttempt, DeliveryRecord, DeliveryStatus
    from signer import WebhookSigner
    from retry_policy import RetryPolicy


# Signature: (url, headers, json_body_str) -> (status_code, error_message)
HttpClient = Callable[[str, Dict[str, str], str], Tuple[Optional[int], Optional[str]]]


class WebhookDispatcher:
    def __init__(self, retry_policy: Optional[RetryPolicy] = None):
        self.retry_policy = retry_policy if retry_policy is not None else RetryPolicy()
        self._endpoints: Dict[str, WebhookEndpoint] = {}
        self._delivery_records: Dict[str, DeliveryRecord] = {}

    def register_endpoint(self, endpoint: WebhookEndpoint) -> None:
        self._endpoints[endpoint.endpoint_id] = endpoint

    def get_endpoint(self, endpoint_id: str) -> Optional[WebhookEndpoint]:
        return self._endpoints.get(endpoint_id)

    def get_delivery_record(self, event_id: str, endpoint_id: str) -> Optional[DeliveryRecord]:
        key = f"{event_id}:{endpoint_id}"
        return self._delivery_records.get(key)

    def dispatch_event(
        self,
        event: WebhookEvent,
        endpoint_id: str,
        http_client: HttpClient,
        current_time: float,
    ) -> DeliveryRecord:
        endpoint = self.get_endpoint(endpoint_id)
        if not endpoint:
            raise ValueError(f"Endpoint {endpoint_id} not found")
        if not endpoint.is_active:
            raise ValueError(f"Endpoint {endpoint_id} is inactive")

        key = f"{event.event_id}:{endpoint_id}"
        record = self._delivery_records.get(key)
        if record is None:
            record = DeliveryRecord(
                event_id=event.event_id,
                endpoint_id=endpoint_id,
                status=DeliveryStatus.PENDING,
                attempts=[],
            )
            self._delivery_records[key] = record

        # Generate signature and prepare payload
        signature_header = WebhookSigner.compute_signature(
            secret=endpoint.secret,
            timestamp=current_time,
            payload=event.payload,
        )

        headers = {
            "Content-Type": "application/json",
            "X-EventBridge-Event": event.event_type,
            "X-EventBridge-Signature": signature_header,
        }

        # Serialized JSON body for delivery
        body_str = json.dumps(event.payload, sort_keys=True, separators=(',', ':'))

        # Perform delivery attempt
        attempt_num = len(record.attempts) + 1
        status_code, error_msg = http_client(endpoint.url, headers, body_str)
        is_success = status_code is not None and 200 <= status_code < 300

        attempt = DeliveryAttempt(
            attempt_number=attempt_num,
            timestamp=current_time,
            status_code=status_code,
            success=is_success,
            error=error_msg,
        )
        record.attempts.append(attempt)

        if is_success:
            record.status = DeliveryStatus.DELIVERED
            record.next_retry_at = None
        else:
            can_retry = (
                self.retry_policy.is_retryable(status_code)
                and attempt_num < self.retry_policy.max_attempts
            )
            if can_retry:
                record.status = DeliveryStatus.RETRYING
                delay = self.retry_policy.compute_next_delay(attempt_num)
                record.next_retry_at = current_time + delay
            else:
                record.status = DeliveryStatus.FAILED
                record.next_retry_at = None

        return record
