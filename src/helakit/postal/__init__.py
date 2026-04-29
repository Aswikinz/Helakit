"""Sri Lankan postal-code validation."""

from helakit.postal.exceptions import PostalError
from helakit.postal.validator import is_valid_postal, validate_postal

__all__ = [
    "PostalError",
    "is_valid_postal",
    "validate_postal",
]
