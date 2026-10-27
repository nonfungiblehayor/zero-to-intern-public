from dataclasses import dataclass
from typing import List, Optional


@dataclass
class OrderLine:
    sku: str
    quantity: int


@dataclass
class ReservationRecord:
    warehouse_id: str
    sku: str
    quantity: int


@dataclass
class AllocationResult:
    order_id: str
    success: bool
    reservations: List[ReservationRecord]
    error_message: Optional[str] = None
