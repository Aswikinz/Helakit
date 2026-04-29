"""The ``Validator`` protocol that every domain validator implements."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from helakit._core.result import ValidationResult


@runtime_checkable
class Validator(Protocol):
    """Structural type for any object that validates Sri Lankan data.

    Implementations expose a short ``name`` (e.g. ``"nic"``) along with two
    parallel entry points: a rich :meth:`validate` returning a
    :class:`~helakit._core.result.ValidationResult`, and a boolean
    :meth:`is_valid` shorthand.
    """

    name: str

    def validate(self, value: str) -> ValidationResult:
        """Run full validation and return a structured result."""
        ...

    def is_valid(self, value: str) -> bool:
        """Return ``True`` if ``value`` is valid, ``False`` otherwise."""
        ...
