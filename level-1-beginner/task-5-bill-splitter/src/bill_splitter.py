"""
bill_splitter.py - Restaurant Dining Bill & Tip Splitter
Calculates tip amounts, gross totals, and equal per-person shares.
"""

from typing import Dict, Any


def calculate_split(total_bill: Any, num_people: Any, tip_percent: Any = 15) -> Dict[str, Any]:
    """
    Calculates per-person payment share including tip.

    Parameters:
    - total_bill: Total meal cost before tip (e.g. 50.00 or '50.00').
    - num_people: Number of people splitting the bill (e.g. 4 or '4').
    - tip_percent: Percentage tip to add (default 15).

    Returns:
    - Dictionary with:
      - 'subtotal': float
      - 'tip_amount': float
      - 'total_with_tip': float
      - 'num_people': int
      - 'per_person': float
    """
    # BUG IDENTIFICATION POINT 1:
    # Missing type coercion: inputs arriving as strings (e.g. from web forms)
    # cause TypeError during mathematical operations.
    # BUG IDENTIFICATION POINT 2:
    # Using integer division '//' instead of floating-point division '/',
    # truncating cents and undercharging each diner!
    # BUG IDENTIFICATION POINT 3:
    # Zero or negative diners causes unhandled ZeroDivisionError.

    tip_amount = round(total_bill * (tip_percent / 100), 2)
    total_with_tip = round(total_bill + tip_amount, 2)

    # Truncating integer division bug:
    per_person = round(total_with_tip // num_people, 2)

    return {
        "subtotal": round(total_bill, 2),
        "tip_percent": tip_percent,
        "tip_amount": tip_amount,
        "total_with_tip": total_with_tip,
        "num_people": num_people,
        "per_person": per_person
    }
