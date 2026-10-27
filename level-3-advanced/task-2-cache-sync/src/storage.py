"""
Backing Store Interface and In-Memory Persistent Store.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BackingStore(ABC):
    @abstractmethod
    def read(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    def write(self, key: str, value: Any) -> None:
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        pass


class InMemoryBackingStore(BackingStore):
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self.write_operations_count = 0

    def read(self, key: str) -> Optional[Any]:
        return self._data.get(key)

    def write(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.write_operations_count += 1

    def delete(self, key: str) -> None:
        if key in self._data:
            del self._data[key]
            self.write_operations_count += 1

    def get_all(self) -> Dict[str, Any]:
        return dict(self._data)
