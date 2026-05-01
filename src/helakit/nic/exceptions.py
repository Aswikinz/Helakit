"""NIC-specific exceptions."""

from __future__ import annotations

from helakit._core.exceptions import HelakitError


class NICError(HelakitError):
    """Base class for NIC-related errors raised by helakit."""


class NICFormatError(NICError):
    """Raised when an input cannot be parsed as either NIC format.

    Used by :func:`helakit.nic.convert_nic` because conversion has no
    sensible ``ValidationResult`` to return — failure must propagate as
    an exception.
    """
