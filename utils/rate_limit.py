"""
PelerProxy Bot — Rate Limit Utils
Daily registration limit enforcement.
"""
import database


def check_rate_limit(user_id: int) -> tuple[bool, str]:
    """
    Check if a user can register today.
    Returns (can_register: bool, reason: str).
    """
    return database.can_register_today(user_id)