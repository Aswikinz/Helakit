"""Result types returned by every validator.

This module defines two dataclasses that every validator in Helakit speaks:

- :class:`ValidationError` — one structured failure.
- :class:`ValidationResult` — the outcome of validating a single value.

Each domain (``phone``, ``nic``, ``postal``, …) returns a subclass of
:class:`ValidationResult` that adds typed properties for the fields it
extracts (carrier, date of birth, district, …). The base class still
works on its own and gives every result a uniform shape: ``is_valid``,
``value``, ``normalized``, ``errors``, ``data``.

Two access patterns are supported, both modelled on pandas:

- Attribute access on the domain subclass: ``result.carrier``.
- Dict-style access on any result: ``result["carrier"]``.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ValidationError:
    """A single validation failure.

    Attributes:
        code: A short machine-readable identifier (e.g. ``"nic.bad_checksum"``).
            Codes are namespaced by domain and are stable across releases —
            check them in tests instead of matching on ``message``.
        message: A human-readable description of what went wrong. Safe to
            show to end users.
        field: The specific field within the input that failed, if applicable.
            ``None`` when the failure is not tied to a single field.

    Example:
        >>> err = ValidationError(
        ...     code="phone.invalid_length",
        ...     message="Sri Lankan phone numbers must be 10 digits.",
        ...     field="value",
        ... )
        >>> err.code
        'phone.invalid_length'
    """

    code: str
    message: str
    field: str | None = None


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """The outcome of validating a single value.

    A ``ValidationResult`` is immutable and *truthy when valid*, so it
    drops naturally into ``if`` statements::

        if validate_phone("0712345678"):
            ...

    Domain-specific subclasses (:class:`~helakit.phone.PhoneResult`,
    :class:`~helakit.nic.NicResult`, :class:`~helakit.postal.PostalResult`)
    add typed properties on top of this shape so you can write
    ``result.carrier`` instead of ``result.data["carrier"]``.

    Attributes:
        is_valid: ``True`` if the input passed every check.
        value: The original input string, unmodified. Useful for echoing
            user input back in error messages.
        normalized: The canonical representation of ``value`` when valid
            (for example ``"+94712345678"`` for a phone number). ``None``
            on invalid results.
        errors: Every error encountered. Empty list when ``is_valid`` is
            ``True``. Errors are reported in the order they were detected;
            validators short-circuit on the first hard failure.
        data: Structured fields extracted during validation (e.g. NIC date
            of birth, phone carrier). Empty when no fields could be
            extracted. Subclasses surface these as typed properties.

    Example:
        >>> from helakit import validate_phone
        >>> result = validate_phone("0712345678")
        >>> result.is_valid
        True
        >>> result.normalized
        '+94712345678'
        >>> result["carrier"]          # dict-style access
        'Mobitel'
        >>> result.carrier             # attribute access (PhoneResult)
        'Mobitel'
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
                f"{type(self).__name__}(is_valid=True, value={self.value!r}, "
                f"normalized={self.normalized!r}, data={self.data!r})"
            )
        codes = [e.code for e in self.errors]
        return f"{type(self).__name__}(is_valid=False, value={self.value!r}, errors={codes!r})"

    def __getitem__(self, key: str) -> Any:
        """Look up an extracted field by name.

        Mirrors the dict-style access pattern people expect from libraries
        like pandas. Raises :class:`KeyError` if the field was not
        extracted (e.g. on invalid input).

        Args:
            key: The name of the field to read from ``data``.

        Returns:
            The value stored in ``data[key]``.

        Raises:
            KeyError: If ``key`` is not present in ``data``.

        Example:
            >>> result = validate_phone("0712345678")
            >>> result["line_type"]
            'mobile'
        """
        return self.data[key]

    def __contains__(self, key: object) -> bool:
        """Return ``True`` if ``key`` is a field that was extracted."""
        return key in self.data

    def __iter__(self) -> Iterator[str]:
        """Iterate over extracted field names, like a dict."""
        return iter(self.data)

    def get(self, key: str, default: Any = None) -> Any:
        """Return ``data[key]`` if present, otherwise ``default``.

        The non-raising counterpart to ``result[key]`` — handy when you
        only want a field if validation actually extracted it.

        Args:
            key: The field name to look up.
            default: Returned when ``key`` is not in ``data``.

        Example:
            >>> result = validate_phone("0712345678")
            >>> result.get("carrier")
            'Mobitel'
            >>> result.get("missing", "n/a")
            'n/a'
        """
        return self.data.get(key, default)
