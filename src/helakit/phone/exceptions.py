"""Phone-specific exceptions."""

from __future__ import annotations

from helakit._core.exceptions import HelakitError


class PhoneError(HelakitError):
    """Raised for unrecoverable phone-related programmer errors."""
