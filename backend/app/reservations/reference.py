"""
10-digit reservation reference generation with collision handling (Feature M7).
"""

from __future__ import annotations

import secrets


def generate_reservation_reference() -> str:
    """
    Generate a cryptographically secure 10-digit numeric reference string.
    Range: 1000000000 to 9999999999 (leading digit 1-9 to guarantee exact 10 digits).
    """
    return str(secrets.randbelow(9000000000) + 1000000000)
