"""Postal-code validation entry points (stub)."""

from __future__ import annotations

from helakit._core.result import ValidationResult


def validate_postal(value: str) -> ValidationResult:
    """Validate a Sri Lankan postal code.

    Args:
        value: A five-digit postal code.

    Returns:
        A :class:`ValidationResult` with the matching district and
        province populated when valid.

    Raises:
        NotImplementedError: Postal-code validation has not been implemented yet.
    """
    raise NotImplementedError("Coming in a future release")


def is_valid_postal(value: str) -> bool:
    """Return ``True`` if ``value`` is a valid Sri Lankan postal code.

    Raises:
        NotImplementedError: Postal-code validation has not been implemented yet.
    """
    raise NotImplementedError("Coming in a future release")
