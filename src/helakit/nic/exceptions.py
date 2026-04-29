"""NIC-specific exceptions."""

from __future__ import annotations

from helakit._core.exceptions import HelakitError


class NICError(HelakitError):
    """Raised for unrecoverable NIC-related programmer errors."""
