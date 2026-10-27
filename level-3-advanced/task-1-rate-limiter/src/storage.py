from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ClientWindowData:
    previous_window_count: int
    current_window_count: int
    current_window_start: float


class SlidingWindowStore:
    """In-memory cache storing request counts across sliding windows."""

    def __init__(self):
        self._data: Dict[str, ClientWindowData] = {}

    def get_client_data(self, client_id: str) -> Optional[ClientWindowData]:
        return self._data.get(client_id)

    def set_client_data(self, client_id: str, data: ClientWindowData) -> None:
        self._data[client_id] = data

    def remove_client(self, client_id: str) -> None:
        if client_id in self._data:
            del self._data[client_id]

    def clear(self) -> None:
        self._data.clear()

    def active_client_count(self) -> int:
        return len(self._data)
