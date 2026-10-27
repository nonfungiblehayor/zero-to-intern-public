"""
profile_sanitizer.py - User Profile Input Sanitizer & Formatter
Cleans user registration payloads: strips whitespace, normalizes casing, and validates formats.
"""

from typing import Dict, Any


def sanitize_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitizes user profile data:
    - Trims leading and trailing whitespace from 'username', 'email', and 'full_name'.
    - Converts 'email' to lowercase.
    - Formats 'full_name' with Title Case (e.g. 'john doe' -> 'John Doe').
    - Evaluates 'is_valid': True if username is non-empty, email contains '@' and '.', and full_name is non-empty.

    Parameters:
    - profile: Dictionary with 'username', 'email', and 'full_name'.

    Returns:
    - Dictionary with sanitized fields and validation flag.
    """
    if not isinstance(profile, dict):
        raise TypeError("profile must be a dictionary.")

    username = profile.get("username", "")
    email = profile.get("email", "")
    full_name = profile.get("full_name", "")

    # Ensure string types
    if not isinstance(username, str) or not isinstance(email, str) or not isinstance(full_name, str):
        raise TypeError("username, email, and full_name must be strings.")

    # Format and clean strings
    username.strip()
    email.strip()
    email.lower()
    full_name.strip()
    full_name.title()

    # Basic email validity check
    is_valid_email = "@" in email and "." in email.split("@")[-1]
    is_valid = bool(username and is_valid_email and full_name)

    return {
        "username": username,
        "email": email,
        "full_name": full_name,
        "is_valid": is_valid
    }
