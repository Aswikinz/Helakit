"""Sri Lankan postal-code validation."""

from helakit.postal._types import (
    PostalBatchResult,
    PostalDecoded,
    PostalResult,
    PostalSummary,
)
from helakit.postal.exceptions import PostalError
from helakit.postal.validator import is_valid_postal, validate_postal

__all__ = [
    "PostalBatchResult",
    "PostalDecoded",
    "PostalError",
    "PostalResult",
    "PostalSummary",
    "is_valid_postal",
    "validate_postal",
]
