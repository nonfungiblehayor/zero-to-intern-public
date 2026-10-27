import math
from models import RateLimitConfig, RateLimitResult
from storage import SlidingWindowStore, ClientWindowData
from clock import Clock


class SlidingWindowRateLimiter:
    """
    Implements the Sliding Window Counter algorithm to estimate request rate
    smoothly without boundary burst anomalies.
    """

    def __init__(self, config: RateLimitConfig, store: SlidingWindowStore, clock: Clock):
        self.config = config
        self.store = store
        self.clock = clock

    def _sync_window(self, client_id: str, now: float) -> ClientWindowData:
        data = self.store.get_client_data(client_id)
        if data is None:
            data = ClientWindowData(
                previous_window_count=0,
                current_window_count=0,
                current_window_start=now
            )
            self.store.set_client_data(client_id, data)
            return data

        elapsed = now - data.current_window_start
        window_duration = self.config.window_seconds

        # Advance window if elapsed time exceeds window duration
        if elapsed >= window_duration:
            data.previous_window_count = data.current_window_count
            data.current_window_count = 0
            data.current_window_start += window_duration

        return data

    def check(self, client_id: str) -> RateLimitResult:
        now = self.clock.now()
        data = self._sync_window(client_id, now)

        window_duration = self.config.window_seconds
        time_into_current = now - data.current_window_start

        # Calculate estimated request count in current sliding window
        weight = time_into_current / window_duration
        estimated_count = (data.previous_window_count * weight) + data.current_window_count

        limit = self.config.limit
        reset_in = max(0.0, window_duration - time_into_current)

        if estimated_count < limit:
            data.current_window_count += 1
            remaining = int(limit - estimated_count - 1)
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=max(0, remaining),
                retry_after=None,
                reset_in=round(reset_in, 2)
            )
        else:
            retry_after = round(reset_in, 2)
            remaining = int(limit - estimated_count - 1)
            return RateLimitResult(
                allowed=False,
                limit=limit,
                remaining=remaining,
                retry_after=retry_after,
                reset_in=round(reset_in, 2)
            )
