class InsufficientStockError(Exception):
    """Raised when a warehouse does not have enough inventory for a SKU."""
    pass


class AllocationError(Exception):
    """Raised when an order cannot be completely fulfilled."""
    pass
