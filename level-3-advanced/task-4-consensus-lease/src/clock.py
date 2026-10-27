class SimulatedClock:
    def __init__(self, start_ms: int = 1000):
        self._current_time_ms = start_ms

    def now_ms(self) -> int:
        return self._current_time_ms

    def advance_ms(self, delta_ms: int) -> int:
        if delta_ms < 0:
            raise ValueError("Time cannot move backwards")
        self._current_time_ms += delta_ms
        return self._current_time_ms
