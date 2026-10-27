"""
temperature_analyzer.py - WeatherStation Temperature Analyzer
Processes temperature reading lists to calculate min, max, average, and freezing status.
"""

from typing import List, Dict, Any, Optional


def analyze_temperatures(readings: List[float]) -> Dict[str, Any]:
    """
    Analyzes a list of numerical temperature readings in Celsius.

    Parameters:
    - readings: List of numeric values (int or float).

    Returns:
    - Dictionary with keys:
      - "min_temp": Lowest recorded temperature (float, or None if readings is empty)
      - "max_temp": Highest recorded temperature (float, or None if readings is empty)
      - "avg_temp": Average temperature rounded to 1 decimal place (float, or None if readings is empty)
      - "reading_count": Total number of readings (int)
      - "is_freezing": True if any reading is <= 0.0, else False
    """
    if not isinstance(readings, list):
        raise TypeError("readings must be a list.")

    for temp in readings:
        if not isinstance(temp, (int, float)) or isinstance(temp, bool):
            raise TypeError("All temperature readings must be numbers (int or float).")

    # Tracking variables
    min_temp = 0.0
    max_temp = 0.0
    total = 0.0
    is_freezing = False

    for temp in readings:
        total += temp
        if temp < min_temp:
            min_temp = temp
        if temp > max_temp:
            max_temp = temp
        if temp <= 0.0:
            is_freezing = True

    avg_temp = round(total / len(readings), 1)

    return {
        "min_temp": float(min_temp),
        "max_temp": float(max_temp),
        "avg_temp": float(avg_temp),
        "reading_count": len(readings),
        "is_freezing": is_freezing
    }
