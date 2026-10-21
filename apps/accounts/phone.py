"""
Bangladesh phone normalization.

Stored form: 01XXXXXXXXX (11 digits).
Accepts: 01…, 8801…, +8801…
"""
import re

from django.core.exceptions import ValidationError

_BD_LOCAL = re.compile(r"^01[3-9]\d{8}$")


def normalize_bd_phone(raw: str) -> str:
    """Normalize user input to 01XXXXXXXXX or raise ValidationError."""
    if raw is None:
        raise ValidationError("Phone number is required.")

    digits = re.sub(r"\D", "", str(raw).strip())

    # +8801XXXXXXXXX / 8801XXXXXXXXX → 01XXXXXXXXX
    if digits.startswith("880"):
        digits = digits[3:]
    if len(digits) == 10 and digits.startswith("1"):
        digits = "0" + digits

    if not _BD_LOCAL.match(digits):
        raise ValidationError(
            "Enter a valid Bangladesh mobile number (e.g. 017XXXXXXXX)."
        )
    return digits
