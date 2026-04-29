"""Exception hierarchy for programmer errors raised by helakit.

Validation *failures* are reported through :class:`ValidationResult` rather
than exceptions; the classes here represent unrecoverable misuse — for
example, passing ``None`` where a string is required.
"""

from __future__ import annotations


class HelakitError(Exception):
    """Base class for every exception raised by helakit."""


class InvalidInputError(HelakitError):
    """Raised when an input is the wrong type or otherwise unusable.

    This signals a programmer error, not a validation failure. A malformed
    NIC string returns a :class:`ValidationResult` with ``is_valid=False``;
    passing ``None`` instead of a string raises this.
    """
