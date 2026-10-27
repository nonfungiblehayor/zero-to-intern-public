"""
cart_pricing.py - E-Commerce Shopping Cart Pricing Engine
Handles cart subtotal, membership tier discounts, shipping fees, tax, and order totals.
"""

from typing import Dict, List, Any

# Membership tier discount rates
TIER_DISCOUNT_RATES = {
    "standard": 0.00,
    "silver": 0.05,    # 5%
    "gold": 0.10,      # 10%
    "platinum": 0.20   # 20%
}

# Standard shipping fee
STANDARD_SHIPPING_FEE = 4.99
FREE_SHIPPING_THRESHOLD = 50.00

# Standard sales tax rate (applied to taxable items)
SALES_TAX_RATE = 0.07  # 7%


def calculate_subtotal(items: List[Dict[str, Any]]) -> float:
    """
    Calculate the gross subtotal of all items in the cart.
    Subtotal = sum(unit_price * quantity)
    """
    subtotal = 0.0
    for item in items:
        price = item.get("price", 0.0)
        quantity = item.get("quantity", 0)
        if price < 0 or quantity < 0:
            raise ValueError("Price and quantity must be non-negative.")
        subtotal += price * quantity
    return round(subtotal, 2)


def calculate_tier_discount(subtotal: float, tier: str) -> float:
    """
    Calculate the membership discount amount for a given subtotal and tier.
    """
    normalized_tier = tier.lower() if tier else "standard"
    discount_rate = TIER_DISCOUNT_RATES.get(normalized_tier, 0.00)
    return round(subtotal * discount_rate, 2)


def calculate_shipping_fee(items: List[Dict[str, Any]], discounted_subtotal: float) -> float:
    """
    Calculate shipping fee based on cart contents and discounted subtotal:
    - If all items in cart are digital (category == 'gift_card'), shipping is $0.00.
    - If discounted subtotal >= $50.00, shipping is $0.00.
    - Otherwise, standard shipping is $4.99.
    - Empty cart incurs $0.00 shipping.
    """
    if not items or discounted_subtotal <= 0:
        return 0.00

    all_digital = all(item.get("category", "").lower() == "gift_card" for item in items)
    if all_digital:
        return 0.00

    if discounted_subtotal >= FREE_SHIPPING_THRESHOLD:
        return 0.00

    return STANDARD_SHIPPING_FEE


def calculate_tax(items: List[Dict[str, Any]], discount_amount: float) -> float:
    """
    Calculate sales tax for taxable items in the cart.
    Gift cards (category == 'gift_card') are tax-exempt.
    Tax is 7% calculated on the taxable amount after discount.
    """
    gross_taxable = sum(
        item.get("price", 0.0) * item.get("quantity", 0)
        for item in items
        if item.get("category", "").lower() != "gift_card"
    )

    if gross_taxable <= 0:
        return 0.00

    net_taxable = max(0.0, gross_taxable - discount_amount)
    return round(net_taxable * SALES_TAX_RATE, 2)


def calculate_order_summary(cart: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates the complete order summary for a given cart.

    Expected Cart structure:
    {
        "customer": {"id": "C-101", "name": "Jane", "tier": "gold"},
        "items": [
            {
                "id": "SKU-1",
                "name": "Mechanical Keyboard",
                "price": 80.00,
                "quantity": 1,
                "category": "electronics",
                "is_discountable": True
            }
        ]
    }
    """
    if not isinstance(cart, dict):
        raise TypeError("Cart must be a dictionary.")

    items = cart.get("items", [])
    customer = cart.get("customer", {})
    tier = customer.get("tier", "standard") if customer else "standard"

    # Step 1: Gross Subtotal
    subtotal = calculate_subtotal(items)

    # Step 2: Tier Discount
    # BUG IDENTIFICATION POINT:
    # The starter code passes the entire subtotal directly to calculate_tier_discount,
    # completely ignoring whether individual items have `is_discountable: False`
    # (such as gift cards or promotional exclusions).
    discount_amount = calculate_tier_discount(subtotal, tier)

    # Step 3: Discounted Subtotal
    discounted_subtotal = round(max(0.0, subtotal - discount_amount), 2)

    # Step 4: Shipping
    shipping_fee = calculate_shipping_fee(items, discounted_subtotal)

    # Step 5: Tax
    tax_amount = calculate_tax(items, discount_amount)

    # Step 6: Total
    total = round(discounted_subtotal + shipping_fee + tax_amount, 2)

    return {
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "discounted_subtotal": discounted_subtotal,
        "shipping_fee": shipping_fee,
        "tax_amount": tax_amount,
        "total": total,
        "item_count": sum(item.get("quantity", 0) for item in items)
    }
