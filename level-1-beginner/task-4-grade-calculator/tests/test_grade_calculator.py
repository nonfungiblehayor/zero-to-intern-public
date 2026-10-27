import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from grade_calculator import assign_letter_grade, calculate_grade_report


class TestGradeCalculator(unittest.TestCase):

    def test_failing_grade_below_60(self):
        """Scores below 60.0 receive an 'F'."""
        self.assertEqual(assign_letter_grade(52.0), "F")

    def test_grade_d_range(self):
        """Scores between 60.0 and 69.9 receive a 'D'."""
        self.assertEqual(assign_letter_grade(65.0), "D")

    def test_bug_reproduction_high_score_overwritten(self):
        """
        REPRODUCTION TEST FOR BUG REPORT #EDU-401:
        A student scoring 95.0 should receive an 'A'.
        Under the bug, independent if statements overwrite 'A' with 'D'!
        """
        self.assertEqual(assign_letter_grade(95.0), "A", "High scores >= 90 must receive an 'A'!")

    def test_bug_reproduction_grade_b_overwritten(self):
        """
        A student scoring 85.0 should receive a 'B'.
        Under the bug, independent if statements overwrite 'B' with 'D'!
        """
        self.assertEqual(assign_letter_grade(85.0), "B", "Scores in the 80s must receive a 'B'!")


if __name__ == "__main__":
    unittest.main()
