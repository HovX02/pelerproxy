"""
PelerProxy Bot — Input Validators
"""
import re


def validate_email(email: str) -> tuple[bool, str]:
    """
    Validate email format.
    Returns (is_valid, error_message).
    """
    email = email.strip()

    if not email:
        return False, "❌ Email cannot be empty."

    if "@" not in email:
        return False, "❌ Invalid email — missing '@'."

    if len(email) > 255:
        return False, "❌ Email too long."

    # Basic regex for reasonable email format
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        return False, "❌ Invalid email format."

    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    Returns (is_valid, error_message).
    """
    password = password.strip()

    if not password:
        return False, "❌ Password cannot be empty."

    if len(password) < 6:
        return False, "❌ Password too short (min 6 characters)."

    if len(password) > 128:
        return False, "❌ Password too long."

    return True, ""