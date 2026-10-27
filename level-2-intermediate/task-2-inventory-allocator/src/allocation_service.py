from typing import List
from models import OrderLine, AllocationResult, ReservationRecord
from warehouse import Warehouse
from exceptions import InsufficientStockError, AllocationError


class AllocationService:
    """Orchestrates order allocation across multiple regional warehouses."""

    def __init__(self, warehouses: List[Warehouse]):
        self.warehouses = warehouses

    def allocate_order(self, order_id: str, lines: List[OrderLine]) -> AllocationResult:
        if not order_id or not isinstance(order_id, str):
            raise ValueError("order_id must be a non-empty string.")
        if not lines or not isinstance(lines, list):
            raise ValueError("lines must be a non-empty list of OrderLine objects.")

        successful_reservations: List[ReservationRecord] = []

        try:
            for line in lines:
                if line.quantity <= 0:
                    raise ValueError(f"Invalid quantity {line.quantity} for {line.sku}.")

                fulfilled = False
                for wh in self.warehouses:
                    if wh.get_available_stock(line.sku) >= line.quantity:
                        wh.reserve(line.sku, line.quantity)
                        successful_reservations.append(ReservationRecord(
                            warehouse_id=wh.warehouse_id,
                            sku=line.sku,
                            quantity=line.quantity
                        ))
                        fulfilled = True
                        break

                if not fulfilled:
                    raise InsufficientStockError(f"Could not fulfill line item {line.sku} across any warehouse.")

            return AllocationResult(
                order_id=order_id,
                success=True,
                reservations=successful_reservations
            )

        except (InsufficientStockError, ValueError) as exc:
            # Catch failure and re-raise AllocationError
            raise AllocationError(f"Allocation failed for order {order_id}: {str(exc)}") from exc
