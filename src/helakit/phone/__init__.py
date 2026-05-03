"""Sri Lankan phone-number validation.

Typical usage::

    import helakit as hk

    result = hk.phone.validate("0712345678")
    result.normalized   # "+94712345678"
    result.data         # {"carrier": "Mobitel", "line_type": "mobile", "local": "0712345678"}

    hk.phone.is_valid("+94762345678")  # True

The original function names are kept as aliases for backwards compatibility::

    from helakit.phone import validate_phone, is_valid_phone
"""

from __future__ import annotations

from helakit.phone.exceptions import PhoneError
from helakit.phone.validator import is_valid_phone, validate_phone

# Clean namespaced API:  hk.phone.validate(...)  /  hk.phone.is_valid(...)
validate = validate_phone
is_valid = is_valid_phone

__all__ = [
    # Namespaced API
    "validate",
    "is_valid",
    # Backwards-compatible names
    "validate_phone",
    "is_valid_phone",
    # Exceptions
    "PhoneError",
]
