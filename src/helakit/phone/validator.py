"""Phone-number validation entry points (stub)."""

from __future__ import annotations

from helakit._core.result import ValidationResult


def validate_phone(value: str) -> ValidationResult:
    """Validate a Sri Lankan phone number.

    Args:
        value: The phone number, either local (``"0712345678"``) or
            international (``"+94712345678"``) form.

    Returns:
        A :class:`ValidationResult` with the carrier and number type
        populated when valid.

    Raises:
        NotImplementedError: Phone validation has not been implemented yet.
    """
    raise NotImplementedError("Coming in a future release")


def is_valid_phone(value: str) -> bool:
    """Return ``True`` if ``value`` is a valid Sri Lankan phone number.

    Raises:
        NotImplementedError: Phone validation has not been implemented yet.
    """
    raise NotImplementedError("Coming in a future release")
