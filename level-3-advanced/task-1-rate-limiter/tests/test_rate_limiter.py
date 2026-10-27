import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from models import RateLimitConfig, ClientRequest
from clock import TestClock
from storage import SlidingWindowStore
from limiter import SlidingWindowRateLimiter
from gateway import APIGateway


class TestRateLimiter(unittest.TestCase):

    def setUp(self):
        self.clock = TestClock(start_time=1000.0)
        self.store = SlidingWindowStore()
        # 10 requests per 60 seconds
        self.config = RateLimitConfig(limit=10, window_seconds=60.0)
        self.limiter = SlidingWindowRateLimiter(self.config, self.store, self.clock)
        self.gateway = APIGateway(self.limiter)

    def test_first_request_allowed(self):
        """Initial request within limit is allowed with proper headers."""
        status, headers, body = self.gateway.handle_request(ClientRequest("client-1", "/api/data", 1000.0))
        self.assertEqual(status, 200)
        self.assertEqual(headers["X-RateLimit-Limit"], "10")
        self.assertEqual(headers["X-RateLimit-Remaining"], "9")

    def test_requests_exceeding_limit_within_single_window_rejected(self):
        """10 requests succeed; 11th request within same window is rejected with 429."""
        client_id = "client-burst"
        for i in range(10):
            status, _, _ = self.gateway.handle_request(ClientRequest(client_id, "/api/data", 1000.0 + i))
            self.assertEqual(status, 200)

        # 11th request
        status, headers, body = self.gateway.handle_request(ClientRequest(client_id, "/api/data", 1015.0))
        self.assertEqual(status, 429)
        self.assertIn("Retry-After", headers)

    def test_bug_reproduction_ticket_gate_401_inverted_sliding_window_weight(self):
        """
        REPRODUCTION TEST 1 (Ticket #GATE-401):
        At t=0, client makes 8 requests.
        At t=60, window rolls over.
        At t=105 (45s into window 2, 75% elapsed):
        - Previous window weight should be (1.0 - 45/60) = 0.25 (25%).
        - Estimated carried-over count should be 8 * 0.25 = 2.0.
        - Client should be permitted 8 additional requests (10 - 2 = 8).
        Under the bug, weight is inverted (45/60 = 0.75), over-penalizing old requests!
        """
        client_id = "client-sliding"
        # Window 1: 8 requests at t=1000
        for _ in range(8):
            self.gateway.handle_request(ClientRequest(client_id, "/api/data", self.clock.now()))

        # Advance time by 105 seconds (45s into second window)
        self.clock.advance(105.0)

        # Client should be able to make at least 7 requests without being blocked
        allowed_count = 0
        for _ in range(8):
            status, _, _ = self.gateway.handle_request(ClientRequest(client_id, "/api/data", self.clock.now()))
            if status == 200:
                allowed_count += 1

        self.assertGreaterEqual(
            allowed_count, 7,
            f"Inverted sliding window weighting rejected legitimate traffic! Allowed only {allowed_count} requests."
        )

    def test_bug_reproduction_ticket_gate_402_long_idle_interval_traffic_resurrection(self):
        """
        REPRODUCTION TEST 2 (Ticket #GATE-402):
        Client sends 10 requests in Window 1, then stays idle for 1 hour (60 full windows).
        Upon return, old counts must not be resurrected into previous_window_count.
        """
        client_id = "client-dormant"
        for _ in range(10):
            self.gateway.handle_request(ClientRequest(client_id, "/api/data", self.clock.now()))

        # Idle for 3600 seconds (1 hour)
        self.clock.advance(3600.0)

        # Client returns: First request must be allowed with 9 remaining!
        status, headers, _ = self.gateway.handle_request(ClientRequest(client_id, "/api/data", self.clock.now()))
        self.assertEqual(status, 200, "Dormant client traffic was resurrected from 1 hour ago!")
        self.assertEqual(headers["X-RateLimit-Remaining"], "9")

    def test_bug_reproduction_ticket_gate_403_negative_remaining_header(self):
        """
        REPRODUCTION TEST 3 (Ticket #GATE-403):
        When requests are rejected, X-RateLimit-Remaining must be clamped at 0, not negative!
        """
        client_id = "client-overflow"
        for _ in range(10):
            self.gateway.handle_request(ClientRequest(client_id, "/api/data", self.clock.now()))

        # Send excess requests
        status, headers, _ = self.gateway.handle_request(ClientRequest(client_id, "/api/data", self.clock.now()))
        self.assertEqual(status, 429)
        self.assertEqual(
            headers["X-RateLimit-Remaining"], "0",
            f"X-RateLimit-Remaining underflowed to negative value: {headers['X-RateLimit-Remaining']}"
        )


if __name__ == "__main__":
    unittest.main()
