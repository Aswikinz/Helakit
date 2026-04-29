"""Helakit — a toolkit for validating and working with Sri Lankan data."""

from helakit._core.exceptions import HelakitError, InvalidInputError
from helakit._core.result import ValidationError, ValidationResult
from helakit.nic import is_valid_nic, validate_nic
from helakit.phone import is_valid_phone, validate_phone
from helakit.postal import is_valid_postal, validate_postal

__version__ = "0.1.0"

__all__ = [
    "HelakitError",
    "InvalidInputError",
    "ValidationError",
    "ValidationResult",
    "__version__",
    "is_valid_nic",
    "is_valid_phone",
    "is_valid_postal",
    "validate_nic",
    "validate_phone",
    "validate_postal",
]
