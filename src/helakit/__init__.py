"""Helakit — a toolkit for validating and working with Sri Lankan data."""

from helakit._core.exceptions import HelakitError, InvalidInputError
from helakit._core.result import ValidationError, ValidationResult
from helakit.nic import (
    NICBatchResult,
    NICDecoded,
    NICError,
    NICFormatError,
    NicResult,
    NICSummary,
    convert_nic,
    is_valid_nic,
    validate_nic,
)
from helakit.phone import PhoneDecoded, PhoneError, PhoneResult, is_valid_phone, validate_phone
from helakit.postal import (
    PostalBatchResult,
    PostalDecoded,
    PostalError,
    PostalResult,
    PostalSummary,
    is_valid_postal,
    validate_postal,
)

__version__ = "0.4.0"

__all__ = [
    "HelakitError",
    "InvalidInputError",
    "NICBatchResult",
    "NICDecoded",
    "NICError",
    "NICFormatError",
    "NICSummary",
    "NicResult",
    "PhoneDecoded",
    "PhoneError",
    "PhoneResult",
    "PostalBatchResult",
    "PostalDecoded",
    "PostalError",
    "PostalResult",
    "PostalSummary",
    "ValidationError",
    "ValidationResult",
    "__version__",
    "convert_nic",
    "is_valid_nic",
    "is_valid_phone",
    "is_valid_postal",
    "validate_nic",
    "validate_phone",
    "validate_postal",
]
