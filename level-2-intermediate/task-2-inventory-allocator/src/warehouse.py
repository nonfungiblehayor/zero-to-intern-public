from typing import Dict
from exceptions import InsufficientStockError


class Warehouse:
    """Represents a physical warehouse holding inventory for SKUs."""

    def __init__(self, warehouse_id: str, name: str):
        self.warehouse_id = warehouse_id
        self.name = name
        self._inventory: Dict[str, int] = {}
        self._reserved: Dict[str, int] = {}

    def set_stock(self, sku: str, quantity: int) -> None:
        self._inventory[sku] = quantity
        self._reserved[sku] = 0

    def get_available_stock(self, sku: str) -> int:
        return self._inventory.get(sku, 0)

    def get_reserved_stock(self, sku: str) -> int:
        return self._reserved.get(sku, 0)

    def reserve(self, sku: str, quantity: int) -> None:
        available = self.get_available_stock(sku)
        if available < quantity:
            raise InsufficientStockError(
                f"Warehouse '{self.warehouse_id}' has only {available} units of {sku}, needed {quantity}."
            )
        self._inventory[sku] = available - quantity
        self._reserved[sku] = self.get_reserved_stock(sku) + quantity

    def release(self, sku: str, quantity: int) -> None:
        reserved = self.get_reserved_stock(sku)
        if reserved < quantity:
            raise ValueError(f"Cannot release {quantity} units of {sku}; only {reserved} reserved.")
        self._reserved[sku] = reserved - quantity
        self._inventory[sku] = self.get_available_stock(sku) + quantity
