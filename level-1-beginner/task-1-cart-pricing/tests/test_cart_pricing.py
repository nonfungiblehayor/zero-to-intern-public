import unittest
import sys
import os

# Add src to sys.path so tests can import cart_pricing directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from cart_pricing import (
    calculate_subtotal,
    calculate_tier_discount,
    calculate_shipping_fee,
    calculate_order_summary
)


class TestCartPricing(unittest.TestCase):

    def test_empty_cart(self):
        """An empty cart should produce zero totals with zero shipping and tax."""
        cart = {"customer": {"tier": "standard"}, "items": []}
        summary = calculate_order_summary(cart)

        self.assertEqual(summary["subtotal"], 0.0)
        self.assertEqual(summary["discount_amount"], 0.0)
        self.assertEqual(summary["discounted_subtotal"], 0.0)
        self.assertEqual(summary["shipping_fee"], 0.0)
        self.assertEqual(summary["tax_amount"], 0.0)
        self.assertEqual(summary["total"], 0.0)
        self.assertEqual(summary["item_count"], 0)

    def test_standard_tier_no_discount(self):
        """Standard tier receives 0% discount."""
        cart = {
            "customer": {"tier": "standard"},
            "items": [
                {
                    "id": "SKU-001",
                    "name": "Notebook",
                    "price": 10.00,
                    "quantity": 2,
                    "category": "stationery",
                    "is_discountable": True
                }
            ]
        }
        summary = calculate_order_summary(cart)

        self.assertEqual(summary["subtotal"], 20.00)
        self.assertEqual(summary["discount_amount"], 0.00)
        self.assertEqual(summary["discounted_subtotal"], 20.00)
        self.assertEqual(summary["shipping_fee"], 4.99)
        # Tax: 7% of 20.00 = 1.40
        self.assertEqual(summary["tax_amount"], 1.40)
        # Total: 20.00 + 4.99 + 1.40 = 26.39
        self.assertEqual(summary["total"], 26.39)
        self.assertEqual(summary["item_count"], 2)

    def test_gold_tier_discountable_items_only(self):
        """Gold tier receives 10% discount on all discountable items."""
        cart = {
            "customer": {"tier": "gold"},
            "items": [
                {
                    "id": "SKU-001",
                    "name": "Wireless Mouse",
                    "price": 30.00,
                    "quantity": 2,
                    "category": "electronics",
                    "is_discountable": True
                }
            ]
        }
        # Subtotal = 60.00
        # Discount = 10% of 60.00 = 6.00
        # Discounted subtotal = 54.00 (qualifies for free shipping >= $50.00)
        # Shipping = 0.00
        # Tax: 7% of 54.00 = 3.78
        # Total: 54.00 + 0.00 + 3.78 = 57.78
        summary = calculate_order_summary(cart)

        self.assertEqual(summary["subtotal"], 60.00)
        self.assertEqual(summary["discount_amount"], 6.00)
        self.assertEqual(summary["discounted_subtotal"], 54.00)
        self.assertEqual(summary["shipping_fee"], 0.00)
        self.assertEqual(summary["tax_amount"], 3.78)
        self.assertEqual(summary["total"], 57.78)

    def test_free_shipping_threshold(self):
        """Orders with discounted subtotal >= $50 qualify for free shipping."""
        items = [
            {
                "id": "SKU-A",
                "name": "Desk Lamp",
                "price": 50.00,
                "quantity": 1,
                "category": "home",
                "is_discountable": True
            }
        ]
        cart = {"customer": {"tier": "standard"}, "items": items}
        summary = calculate_order_summary(cart)

        self.assertEqual(summary["discounted_subtotal"], 50.00)
        self.assertEqual(summary["shipping_fee"], 0.00)

    def test_bug_reproduction_mixed_discountable_and_gift_card(self):
        """
        REPRODUCTION TEST FOR BUG REPORT #ENG-104:
        A Gold tier member buys:
        - 1x Wireless Mouse ($25.00, is_discountable=True)
        - 1x Digital Gift Card ($50.00, is_discountable=False)

        Expected:
        - Subtotal: $75.00
        - Eligible for discount: $25.00 (the mouse only)
        - Gold Tier Discount (10%): $2.50 (NOT $7.50!)
        - Discounted Subtotal: $72.50
        - Shipping: Free ($0.00 because $72.50 >= $50.00)
        - Tax: 7% of ($25.00 - $2.50) = 7% of $22.50 = $1.58 (Gift cards are tax exempt)
        - Total: $72.50 + $0.00 + $1.58 = $74.08
        """
        cart = {
            "customer": {"tier": "gold"},
            "items": [
                {
                    "id": "SKU-001",
                    "name": "Wireless Mouse",
                    "price": 25.00,
                    "quantity": 1,
                    "category": "electronics",
                    "is_discountable": True
                },
                {
                    "id": "SKU-GIFT",
                    "name": "Digital Gift Card",
                    "price": 50.00,
                    "quantity": 1,
                    "category": "gift_card",
                    "is_discountable": False
                }
            ]
        }
        summary = calculate_order_summary(cart)

        self.assertEqual(summary["subtotal"], 75.00)
        # Under the bug, discount_amount evaluates to 7.50 instead of 2.50!
        self.assertEqual(summary["discount_amount"], 2.50)
        self.assertEqual(summary["discounted_subtotal"], 72.50)
        self.assertEqual(summary["shipping_fee"], 0.00)
        self.assertEqual(summary["tax_amount"], 1.58)
        self.assertEqual(summary["total"], 74.08)


if __name__ == "__main__":
    unittest.main()
