"""
Time Provider Interface and Clocks for Deterministic Testing.
"""
from abc import ABC, abstractmethod
import time


class Clock(ABC):
    @abstractmethod
    def now(self) -> float:
        """Returns the current monotonic/epoch timestamp in seconds."""
        pass


class SystemClock(Clock):
    def now(self) -> float:
        return time.time()


class TestClock(Clock):
    def __init__(self, initial_time: float = 1000.0):
        self._current_time = initial_time

    def now(self) -> float:
        return self._current_time

    def advance(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError("Cannot move clock backward")
        self._current_time += seconds

    def set_time(self, timestamp: float) -> None:
        if timestamp < self._current_time:
            raise ValueError("Cannot move clock backward")
        self._current_time = timestamp
