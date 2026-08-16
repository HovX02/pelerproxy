"""
PelerProxy Bot — Email Generator
Generates disposable @nullz.in email addresses for automatic registration.
"""
import random
import string
import logging

import config

log = logging.getLogger("pelerproxy.email")


def generate_nullz_username() -> str:
    """Generate a random username for nullz.in email."""
    random_part = "".join(
        random.choices(string.ascii_lowercase + string.digits, k=random.randint(4, 6))
    )
    return f"fakeprithvi{random_part}"


async def create_nullz_email() -> tuple[str, str]:
    """
    Generate a disposable email + password pair.
    Returns (email, password).
    """
    username = generate_nullz_username()
    email = f"{username}@nullz.in"
    password = config.FIXED_PASSWORD
    log.info(f"[NULLZ] Generated: {email}")
    return email, password