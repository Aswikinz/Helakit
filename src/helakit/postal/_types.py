"""Typed result payloads for the postal-code validator."""

from __future__ import annotations

from dataclasses import dataclass

from helakit._core.result import ValidationResult


@dataclass(frozen=True, slots=True)
class PostalDecoded:
    """Structured metadata about a recognised Sri Lankan postal code.

    Returned in ``PostalResult.data["decoded"]`` and accessible as
    ``PostalResult.decoded``.

    Attributes:
        district: The district the code belongs to (e.g. ``"Colombo"``).
        province: The province the district is in (e.g. ``"Western"``).
        post_office: The specific post office name, when known.
    """

    district: str
    province: str
    post_office: str | None = None


class PostalResult(ValidationResult):
    """Validation result returned by
    :func:`~helakit.postal.validate_postal`.

    Typed property accessors mirror the keys placed in ``data`` by the
    validator. Properties return ``None`` on invalid results.

    !!! warning "Planned API"
        Postal-code validation is not implemented yet; this class is
        wired up in advance so the planned shape can be documented and
        imported. Calling :func:`~helakit.postal.validate_postal`
        currently raises ``NotImplementedError``.
    """

    __slots__ = ()

    @property
    def district(self) -> str | None:
        """District name. ``None`` if invalid."""
        return self.data.get("district")

    @property
    def province(self) -> str | None:
        """Province name. ``None`` if invalid."""
        return self.data.get("province")

    @property
    def post_office(self) -> str | None:
        """Post office name, when known. ``None`` otherwise."""
        return self.data.get("post_office")

    @property
    def decoded(self) -> PostalDecoded | None:
        """Full :class:`PostalDecoded` payload. ``None`` if invalid."""
        return self.data.get("decoded")
