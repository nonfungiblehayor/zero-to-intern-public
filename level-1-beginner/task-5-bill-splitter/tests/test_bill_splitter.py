import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from bill_splitter import calculate_split


class TestBillSplitter(unittest.TestCase):

    def test_exact_even_split(self):
        """Even division without fractional cents."""
        result = calculate_split(100.0, 2, tip_percent=10)
        self.assertEqual(result["tip_amount"], 10.00)
        self.assertEqual(result["total_with_tip"], 110.00)
        self.assertEqual(result["per_person"], 55.00)

    def test_bug_reproduction_fractional_cents_truncated(self):
        """
        REPRODUCTION TEST 1 (Ticket #PAY-501):
        A bill of $50.00 split among 4 people with 15% tip ($7.50).
        Total with tip: $57.50.
        Expected per person: $57.50 / 4 = $14.38 (rounded).
        Under the bug, integer division // truncates to $14.00, shortchanging the bill by $1.50!
        """
        result = calculate_split(50.00, 4, tip_percent=15)
        self.assertEqual(result["tip_amount"], 7.50)
        self.assertEqual(result["total_with_tip"], 57.50)
        self.assertEqual(result["per_person"], 14.38, "Per-person share must preserve decimal cents!")

    def test_bug_reproduction_string_inputs_from_form(self):
        """
        REPRODUCTION TEST 2 (Ticket #PAY-502):
        Inputs received as numeric strings from a form payload (e.g. '60.00', '3', '20')
        must be safely converted and calculated.
        Under the bug, multiplying string * float raises a TypeError!
        """
        result = calculate_split("60.00", "3", "20")
        self.assertEqual(result["subtotal"], 60.00)
        self.assertEqual(result["tip_amount"], 12.00)
        self.assertEqual(result["total_with_tip"], 72.00)
        self.assertEqual(result["per_person"], 24.00)


if __name__ == "__main__":
    unittest.main()
