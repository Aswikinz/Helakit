"""Sri Lankan postal-code validation."""

from helakit.postal._types import PostalDecoded, PostalResult
from helakit.postal.exceptions import PostalError
from helakit.postal.validator import is_valid_postal, validate_postal

__all__ = [
    "PostalDecoded",
    "PostalError",
    "PostalResult",
    "is_valid_postal",
    "validate_postal",
]
