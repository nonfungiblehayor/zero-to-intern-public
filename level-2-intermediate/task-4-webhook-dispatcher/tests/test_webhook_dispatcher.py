"""
Unit tests for EventBridge Webhook Dispatcher.
"""
import unittest
import json
import os
import sys

# Ensure src is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from models import WebhookEndpoint, WebhookEvent, DeliveryStatus
from signer import WebhookSigner
from retry_policy import RetryPolicy
from dispatcher import WebhookDispatcher


class TestWebhookDispatcher(unittest.TestCase):
    def setUp(self):
        self.endpoint = WebhookEndpoint(
            endpoint_id="ep_01",
            url="https://api.partner.com/webhooks",
            secret="whsec_test_secret_key_12345",
        )
        self.dispatcher = WebhookDispatcher(RetryPolicy(max_attempts=3, initial_delay=1.0, backoff_factor=2.0))
        self.dispatcher.register_endpoint(self.endpoint)

    def test_basic_successful_delivery(self):
        """Standard HTTP 200 delivery marks delivery as DELIVERED."""
        event = WebhookEvent(
            event_id="evt_100",
            event_type="order.created",
            payload={"order_id": "ord_99", "amount": 150.0},
            timestamp=1000.0,
        )

        def mock_client(url, headers, body):
            return 200, None

        record = self.dispatcher.dispatch_event(event, "ep_01", mock_client, current_time=1000.0)
        self.assertEqual(record.status, DeliveryStatus.DELIVERED)
        self.assertEqual(len(record.attempts), 1)
        self.assertTrue(record.attempts[0].success)

    def test_bug_reproduction_ticket_hook_401_canonical_json_hmac(self):
        """
        REPRODUCTION TEST 1 (Ticket #HOOK-401):
        When signature is computed, it must be verifiable against the standard canonical
        JSON payload bytes sent across the wire.
        """
        payload = {"customer": "Alice", "items": [{"id": 1, "name": "Book"}], "priority": True}
        timestamp = 1700000000.0

        sig_header = WebhookSigner.compute_signature(
            secret=self.endpoint.secret,
            timestamp=timestamp,
            payload=payload,
        )

        # Partner verifies using canonical JSON payload bytes:
        canonical_json_bytes = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode("utf-8")
        is_valid = WebhookSigner.verify_signature(
            secret=self.endpoint.secret,
            signature_header=sig_header,
            canonical_json_bytes=canonical_json_bytes,
        )
        self.assertTrue(
            is_valid,
            "Signature verification failed on consumer end! Signature was computed over invalid non-canonical format."
        )

    def test_bug_reproduction_ticket_hook_402_client_4xx_should_not_retry(self):
        """
        REPRODUCTION TEST 2 (Ticket #HOOK-402):
        Client 4xx errors (e.g. 401 Unauthorized, 404 Not Found) are permanent
        failures and must immediately transition to FAILED without scheduling retries.
        """
        event = WebhookEvent(
            event_id="evt_401",
            event_type="invoice.paid",
            payload={"invoice_id": "inv_123"},
            timestamp=1000.0,
        )

        def client_401(url, headers, body):
            return 401, "Unauthorized"

        record = self.dispatcher.dispatch_event(event, "ep_01", client_401, current_time=1000.0)
        self.assertEqual(
            record.status,
            DeliveryStatus.FAILED,
            "Client 4xx errors should not be retried!"
        )
        self.assertIsNone(record.next_retry_at)

    def test_bug_reproduction_ticket_hook_403_exponential_backoff_progression(self):
        """
        REPRODUCTION TEST 3 (Ticket #HOOK-403):
        Retries must back off exponentially:
        Attempt 1 failure: delay = 1.0s (1.0 * 2^0)
        Attempt 2 failure: delay = 2.0s (1.0 * 2^1)
        Attempt 3 failure: delay = 4.0s (1.0 * 2^2)
        """
        policy = RetryPolicy(max_attempts=4, initial_delay=1.0, backoff_factor=2.0)
        delay_1 = policy.compute_next_delay(attempt_count=1)
        delay_2 = policy.compute_next_delay(attempt_count=2)
        delay_3 = policy.compute_next_delay(attempt_count=3)

        self.assertEqual(delay_1, 1.0, f"Expected 1.0s, got {delay_1}")
        self.assertEqual(delay_2, 2.0, f"Expected 2.0s, got {delay_2}")
        self.assertEqual(delay_3, 4.0, f"Expected 4.0s, got {delay_3}")


if __name__ == "__main__":
    unittest.main()
