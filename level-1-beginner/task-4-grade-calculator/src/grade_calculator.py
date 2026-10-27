"""
grade_calculator.py - Student Grade & Performance Classifier
Assigns letter grades and calculates GPA points from numerical scores.
"""

from typing import Dict, Any


def assign_letter_grade(score: float, has_extra_credit: bool = False) -> str:
    """
    Assigns a letter grade (A, B, C, D, F) based on a percentage score:
    - 90.0 and above: 'A'
    - 80.0 to 89.9:   'B'
    - 70.0 to 79.9:   'C'
    - 60.0 to 69.9:   'D'
    - Below 60.0:     'F'

    Parameters:
    - score: Student score (0.0 to 100.0).
    - has_extra_credit: If True, adds 5 bonus points (capped at 100.0).

    Returns:
    - Letter grade string ('A', 'B', 'C', 'D', 'F').
    """
    if not isinstance(score, (int, float)):
        raise TypeError("Score must be a numeric integer or float.")

    if score < 0.0 or score > 100.0:
        raise ValueError(f"Score {score} is out of valid range (0 to 100).")

    final_score = score
    if has_extra_credit:
        final_score = min(100.0, final_score + 5.0)

    # BUG IDENTIFICATION POINT:
    # Using independent 'if' statements instead of 'if / elif / else' control flow!
    # A score of 95 satisfies (>= 90), setting grade = 'A'.
    # But it also satisfies (>= 80), (>= 70), (>= 60), overwriting grade with 'D'!
    grade = "F"
    if final_score >= 90.0:
        grade = "A"
    if final_score >= 80.0:
        grade = "B"
    if final_score >= 70.0:
        grade = "C"
    if final_score >= 60.0:
        grade = "D"

    return grade


def calculate_grade_report(student_name: str, score: float, has_extra_credit: bool = False) -> Dict[str, Any]:
    """
    Generates a student grade report.
    """
    if not isinstance(student_name, str) or not student_name.strip():
        raise ValueError("student_name must be a non-empty string.")

    letter_grade = assign_letter_grade(score, has_extra_credit)

    # GPA mapping
    gpa_scale = {
        "A": 4.0,
        "B": 3.0,
        "C": 2.0,
        "D": 1.0,
        "F": 0.0
    }

    return {
        "student_name": student_name.strip(),
        "original_score": score,
        "letter_grade": letter_grade,
        "gpa_points": gpa_scale[letter_grade],
        "is_passing": letter_grade in {"A", "B", "C"}
    }
