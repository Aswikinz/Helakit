"""Result types returned by every validator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ValidationError:
    """A single validation failure.

    Attributes:
        code: A short machine-readable identifier (e.g. ``"nic.bad_checksum"``).
        message: A human-readable description of what went wrong.
        field: The specific field within the input that failed, if applicable.
    """

    code: str
    message: str
    field: str | None = None


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """The outcome of validating a single value.

    Attributes:
        is_valid: ``True`` if the input passed every check.
        value: The original input string, unmodified.
        normalized: The canonical representation of ``value`` when valid.
        errors: Every error encountered. Empty when ``is_valid`` is ``True``.
        data: Structured fields extracted during validation (e.g. NIC date of
            birth, gender). Empty when no fields could be extracted.
    """

    is_valid: bool
    value: str
    normalized: str | None = None
    errors: list[ValidationError] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.is_valid

    def __repr__(self) -> str:
        if self.is_valid:
            return (
                f"ValidationResult(is_valid=True, value={self.value!r}, "
                f"normalized={self.normalized!r}, data={self.data!r})"
            )
        codes = [e.code for e in self.errors]
        return f"ValidationResult(is_valid=False, value={self.value!r}, errors={codes!r})"
