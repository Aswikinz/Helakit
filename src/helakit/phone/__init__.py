"""Sri Lankan phone-number validation.

Typical usage::

    import helakit as hk

    result = hk.validate_phone("0712345678")
    result.normalized   # "+94712345678"
    result.data         # PhoneDecoded(carrier="Mobitel", line_type="mobile", local="0712345678")

    hk.is_valid_phone("+94762345678")  # True
"""

from __future__ import annotations

from helakit.phone._types import PhoneDecoded
from helakit.phone.exceptions import PhoneError
from helakit.phone.validator import is_valid_phone, validate_phone

__all__ = [
    "PhoneDecoded",
    "PhoneError",
    "is_valid_phone",
    "validate_phone",
]
