import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from temperature_analyzer import analyze_temperatures


class TestTemperatureAnalyzer(unittest.TestCase):

    def test_mixed_temperature_readings(self):
        """Mixed temperatures spanning sub-zero and above zero."""
        readings = [-5.0, 0.0, 15.0, 10.0]
        result = analyze_temperatures(readings)
        self.assertEqual(result["reading_count"], 4)
        self.assertEqual(result["min_temp"], -5.0)
        self.assertEqual(result["max_temp"], 15.0)
        self.assertEqual(result["avg_temp"], 5.0)
        self.assertTrue(result["is_freezing"])

    def test_bug_reproduction_all_warm_readings_min_zero(self):
        """
        REPRODUCTION TEST 1 (Ticket #STATION-101):
        When all readings are well above freezing (summer day), min_temp should
        be the lowest reading (e.g. 18.5), but the buggy code outputs 0.0!
        """
        readings = [18.5, 22.0, 25.4, 21.0]
        result = analyze_temperatures(readings)
        self.assertEqual(result["min_temp"], 18.5, "min_temp incorrectly defaulted to 0.0 on warm day!")
        self.assertEqual(result["max_temp"], 25.4)
        self.assertFalse(result["is_freezing"])

    def test_bug_reproduction_all_subzero_readings_max_zero(self):
        """
        REPRODUCTION TEST 2 (Ticket #STATION-102):
        When all readings are below freezing (winter arctic vortex), max_temp should
        be the highest reading (e.g. -3.5), but the buggy code outputs 0.0!
        """
        readings = [-15.0, -8.2, -3.5, -12.0]
        result = analyze_temperatures(readings)
        self.assertEqual(result["max_temp"], -3.5, "max_temp incorrectly defaulted to 0.0 in winter!")
        self.assertEqual(result["min_temp"], -15.0)
        self.assertTrue(result["is_freezing"])

    def test_bug_reproduction_empty_readings_division_by_zero(self):
        """
        REPRODUCTION TEST 3 (Ticket #STATION-103):
        When no readings are available ([]), the analyzer must not crash with
        ZeroDivisionError. It should return a safe dictionary with None for extrema/avg.
        """
        result = analyze_temperatures([])
        self.assertEqual(result["reading_count"], 0)
        self.assertIsNone(result["min_temp"])
        self.assertIsNone(result["max_temp"])
        self.assertIsNone(result["avg_temp"])
        self.assertFalse(result["is_freezing"])


if __name__ == "__main__":
    unittest.main()
