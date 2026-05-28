"""Typed result payloads for the phone validator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from helakit._core.result import ValidationResult

LineType = Literal["mobile", "fixed"]


@dataclass(frozen=True, slots=True)
class PhoneDecoded:
    """Structured metadata about a recognised Sri Lankan phone number.

    Returned in ``PhoneResult.data["decoded"]`` and also accessible as
    ``PhoneResult.decoded``. Bundles the three pieces of information that
    can be derived from a number's prefix.

    Attributes:
        carrier: Network operator name (e.g. ``"Dialog"``, ``"Mobitel"``,
            ``"SLT"``). Determined by the three-digit local prefix.
        line_type: Either ``"mobile"`` or ``"fixed"``.
        local: The 10-digit local form (``"0XXXXXXXXX"``). The
            international form is on the result as ``normalized``.

    Example:
        >>> result = validate_phone("+94712345678")
        >>> result.decoded
        PhoneDecoded(carrier='Mobitel', line_type='mobile', local='0712345678')
    """

    carrier: str
    line_type: LineType
    local: str


class PhoneResult(ValidationResult):
    """Validation result returned by :func:`~helakit.phone.validate_phone`.

    Adds typed property accessors for every field the phone validator
    extracts. The underlying ``data`` dict is still populated for
    backwards compatibility, so every access style works::

        result.carrier        # typed property — preferred
        result["carrier"]     # dict-style access
        result.data["carrier"]  # original form

    Properties return ``None`` on invalid results so attribute access
    never raises — guard with ``if result:`` or ``if result.is_valid:``.
    """

    __slots__ = ()

    @property
    def carrier(self) -> str | None:
        """Network operator name, e.g. ``"Dialog"``. ``None`` if invalid."""
        return self.data.get("carrier")

    @property
    def line_type(self) -> LineType | None:
        """``"mobile"`` or ``"fixed"``. ``None`` if invalid."""
        return self.data.get("line_type")

    @property
    def local(self) -> str | None:
        """10-digit local form ``"0XXXXXXXXX"``. ``None`` if invalid."""
        return self.data.get("local")

    @property
    def decoded(self) -> PhoneDecoded | None:
        """Full :class:`PhoneDecoded` payload. ``None`` if invalid."""
        return self.data.get("decoded")
