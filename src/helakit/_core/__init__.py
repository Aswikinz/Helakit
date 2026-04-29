"""Core primitives: ``ValidationResult``, the ``Validator`` protocol, and exceptions."""

from helakit._core.base import Validator
from helakit._core.exceptions import HelakitError, InvalidInputError
from helakit._core.result import ValidationError, ValidationResult

__all__ = [
    "HelakitError",
    "InvalidInputError",
    "ValidationError",
    "ValidationResult",
    "Validator",
]
