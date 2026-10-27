"""
EventBridge Webhook Exponential Backoff and Retry Policy.
"""
from typing import Optional


class RetryPolicy:
    def __init__(self, max_attempts: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor

    def is_retryable(self, status_code: Optional[int]) -> bool:
        """
        Determines if a delivery failure should be retried.
        Network errors (status_code is None) or 5xx server errors (500, 502, 503, 504) are retryable.
        4xx client errors (400, 401, 403, 404, 422) are non-retryable and must fail immediately.
        """
        # DEFECT (Ticket #HOOK-402): Treating any non-200 code as retryable.
        # This causes client 4xx errors (e.g. 401 Unauthorized, 404 Not Found)
        # to be retried repeatedly, spamming downstream endpoints.
        if status_code is None:
            return True
        return status_code != 200

    def compute_next_delay(self, attempt_count: int) -> float:
        """
        Calculates exponential backoff delay for the next attempt:
        delay = initial_delay * (backoff_factor ** (attempt_count - 1))
        e.g. Attempt 1 failure -> delay = 1.0 * (2^0) = 1.0s
             Attempt 2 failure -> delay = 1.0 * (2^1) = 2.0s
             Attempt 3 failure -> delay = 1.0 * (2^2) = 4.0s
        """
        # DEFECT (Ticket #HOOK-403): Fixed delay calculation ignoring attempt count power!
        return self.initial_delay * self.backoff_factor
