import time


class Clock:
    """Time provider interface to allow deterministic time travel in tests."""

    def now(self) -> float:
        return time.time()


class TestClock(Clock):
    """Deterministic clock controllable in unit tests."""

    def __init__(self, start_time: float = 1000.0):
        self._current_time = start_time

    def now(self) -> float:
        return self._current_time

    def advance(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError("Time cannot move backward.")
        self._current_time += seconds

    def set_time(self, timestamp: float) -> None:
        self._current_time = timestamp
