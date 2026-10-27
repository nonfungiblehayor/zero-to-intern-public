import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from models import OrderLine
from warehouse import Warehouse
from allocation_service import AllocationService
from exceptions import AllocationError


class TestAllocationService(unittest.TestCase):

    def setUp(self):
        self.wh_east = Warehouse("WH-EAST", "East Coast Distribution")
        self.wh_west = Warehouse("WH-WEST", "West Coast Hub")
        self.service = AllocationService([self.wh_east, self.wh_west])

    def test_successful_single_warehouse_allocation(self):
        """Order can be fully fulfilled by a single warehouse."""
        self.wh_east.set_stock("SKU-KEYBOARD", 10)
        lines = [OrderLine(sku="SKU-KEYBOARD", quantity=2)]

        result = self.service.allocate_order("ORD-100", lines)
        self.assertTrue(result.success)
        self.assertEqual(len(result.reservations), 1)
        self.assertEqual(self.wh_east.get_available_stock("SKU-KEYBOARD"), 8)
        self.assertEqual(self.wh_east.get_reserved_stock("SKU-KEYBOARD"), 2)

    def test_successful_multi_warehouse_split_allocation(self):
        """Different line items fulfilled across different warehouses."""
        self.wh_east.set_stock("SKU-MOUSE", 5)
        self.wh_west.set_stock("SKU-MONITOR", 3)

        lines = [
            OrderLine(sku="SKU-MOUSE", quantity=1),
            OrderLine(sku="SKU-MONITOR", quantity=2)
        ]
        result = self.service.allocate_order("ORD-101", lines)
        self.assertTrue(result.success)
        self.assertEqual(len(result.reservations), 2)
        self.assertEqual(self.wh_east.get_available_stock("SKU-MOUSE"), 4)
        self.assertEqual(self.wh_west.get_available_stock("SKU-MONITOR"), 1)

    def test_bug_reproduction_ticket_ship_301_zombie_reservation_on_partial_failure(self):
        """
        REPRODUCTION TEST 1 (Ticket #SHIP-301):
        When a multi-item order fails midway due to insufficient stock for a later item,
        all previously reserved items MUST be rolled back (released) immediately.
        Under the bug, partial reservations are never released, creating zombie reservations!
        """
        self.wh_east.set_stock("SKU-LAPTOP", 5)
        self.wh_west.set_stock("SKU-DOCK", 0)   # Out of stock!

        order_lines = [
            OrderLine(sku="SKU-LAPTOP", quantity=3),
            OrderLine(sku="SKU-DOCK", quantity=1)    # Will fail!
        ]

        with self.assertRaises(AllocationError):
            self.service.allocate_order("ORD-FAIL-1", order_lines)

        # Verification of state rollback
        self.assertEqual(
            self.wh_east.get_available_stock("SKU-LAPTOP"), 5,
            "Zombie reservation detected! Available stock was not restored after failed order."
        )
        self.assertEqual(
            self.wh_east.get_reserved_stock("SKU-LAPTOP"), 0,
            "Reserved stock should be 0 after failed order rollback."
        )

    def test_bug_reproduction_ticket_ship_302_invalid_line_item_rollbacks_prior_reservations(self):
        """
        REPRODUCTION TEST 2 (Ticket #SHIP-302):
        If an order line fails validation (e.g. quantity <= 0), prior reserved items must roll back.
        """
        self.wh_east.set_stock("SKU-CABLE", 20)
        order_lines = [
            OrderLine(sku="SKU-CABLE", quantity=4),
            OrderLine(sku="SKU-BAD", quantity=-1)   # Invalid quantity!
        ]

        with self.assertRaises(AllocationError):
            self.service.allocate_order("ORD-FAIL-2", order_lines)

        self.assertEqual(self.wh_east.get_available_stock("SKU-CABLE"), 20)
        self.assertEqual(self.wh_east.get_reserved_stock("SKU-CABLE"), 0)


if __name__ == "__main__":
    unittest.main()
