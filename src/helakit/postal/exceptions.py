"""Postal-code-specific exceptions."""

from __future__ import annotations

from helakit._core.exceptions import HelakitError


class PostalError(HelakitError):
    """Raised for unrecoverable postal-code-related programmer errors."""
