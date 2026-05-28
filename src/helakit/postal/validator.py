"""Postal-code validation entry points (stub)."""

from __future__ import annotations

from helakit.postal._types import PostalResult


def validate_postal(value: str) -> PostalResult:
    """Validate a Sri Lankan postal code.

    Args:
        value: A five-digit postal code.

    Returns:
        A :class:`~helakit.postal.PostalResult` with the matching
        district and province populated when valid. Accessible as
        ``result.district`` / ``result.province`` or via
        ``result["district"]``.

    Raises:
        NotImplementedError: Postal-code validation has not been
            implemented yet.
    """
    raise NotImplementedError("Coming in a future release")


def is_valid_postal(value: str) -> bool:
    """Return ``True`` if ``value`` is a valid Sri Lankan postal code.

    Raises:
        NotImplementedError: Postal-code validation has not been
            implemented yet.
    """
    raise NotImplementedError("Coming in a future release")
