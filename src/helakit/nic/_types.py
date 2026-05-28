"""Public dataclasses returned by the NIC validator."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal

from helakit._core.result import ValidationResult


@dataclass(frozen=True, slots=True)
class NICDecoded:
    """Structured fields extracted from a valid NIC.

    Attributes:
        format: Either ``"old"`` (9 digits + V/X) or ``"new"`` (12 digits).
        dob: Decoded date of birth.
        gender: Either ``"male"`` or ``"female"``, derived from the
            day-of-year encoding.
        age: Age in completed years at the time of validation.
        year: Full birth year.
        day_code: Day-of-year encoding with the female 500 offset removed.
        serial: Serial number assigned on the registration day.
        check_digit: Final check digit (not currently verified — see
            :mod:`helakit.nic._parse`).
        voting_eligible: ``True`` if the old NIC ends in ``V``, ``False``
            if ``X``, ``None`` for new-format NICs.
    """

    format: Literal["old", "new"]
    dob: date
    gender: Literal["male", "female"]
    age: int
    year: int
    day_code: int
    serial: int
    check_digit: int
    voting_eligible: bool | None


class NicResult(ValidationResult):
    """Validation result returned by :func:`~helakit.nic.validate_nic`.

    Adds typed property accessors for every field the NIC validator
    extracts, including pass-through accessors that reach into
    :class:`NICDecoded` so the most commonly-used fields are one
    attribute away::

        result.decoded.dob   # works
        result.dob           # also works — same value

    Properties return ``None`` on invalid results so attribute access
    never raises — guard with ``if result:`` before reading.
    """

    __slots__ = ()

    @property
    def decoded(self) -> NICDecoded | None:
        """Full :class:`NICDecoded` payload. ``None`` if invalid."""
        return self.data.get("decoded")

    @property
    def format(self) -> Literal["old", "new"] | None:
        """``"old"`` or ``"new"``. ``None`` if invalid."""
        return self.data.get("format")

    # --- Pass-through to `decoded` for ergonomics ---------------------------

    @property
    def dob(self) -> date | None:
        """Decoded date of birth. ``None`` if invalid."""
        decoded = self.decoded
        return decoded.dob if decoded else None

    @property
    def gender(self) -> Literal["male", "female"] | None:
        """``"male"`` or ``"female"``. ``None`` if invalid."""
        decoded = self.decoded
        return decoded.gender if decoded else None

    @property
    def age(self) -> int | None:
        """Age in completed years at validation time. ``None`` if invalid."""
        decoded = self.decoded
        return decoded.age if decoded else None

    @property
    def year(self) -> int | None:
        """Full birth year. ``None`` if invalid."""
        decoded = self.decoded
        return decoded.year if decoded else None

    @property
    def serial(self) -> int | None:
        """Serial number assigned on the registration day. ``None`` if invalid."""
        decoded = self.decoded
        return decoded.serial if decoded else None

    @property
    def voting_eligible(self) -> bool | None:
        """``True`` / ``False`` for old NICs; ``None`` for new NICs or
        invalid results."""
        decoded = self.decoded
        return decoded.voting_eligible if decoded else None

    # --- Cross-check results (only populated when dob_col / gender_col
    #     are supplied in batch mode) -----------------------------------------

    @property
    def dob_match(self) -> bool | None:
        """``True`` / ``False`` if a DOB was cross-checked; ``None`` otherwise."""
        return self.data.get("dob_match")

    @property
    def gender_match(self) -> bool | None:
        """``True`` / ``False`` if a gender was cross-checked; ``None`` otherwise."""
        return self.data.get("gender_match")

    @property
    def mismatch_reasons(self) -> list[str] | None:
        """Which cross-check fields disagreed with the NIC. ``None`` when
        no cross-check ran."""
        return self.data.get("mismatch_reasons")

    @property
    def mismatch_detail(self) -> str | None:
        """Human-readable diff of cross-check vs decoded. ``None`` when
        no cross-check ran or everything matched."""
        return self.data.get("mismatch_detail")


@dataclass(frozen=True, slots=True)
class NICSummary:
    """Aggregate counts for a batch validation run.

    Attributes:
        total: Number of input rows processed.
        valid: Rows whose NIC passed structural validation.
        invalid: Rows that failed structural validation.
        duplicate_groups: Number of distinct NICs that appear in more than
            one row (after canonicalisation that strips V/X suffixes).
        duplicate_rows: Total rows participating in any duplicate group.
        dob_mismatches: Rows where the supplied DOB differed from the
            NIC-decoded DOB (only counted when both were available).
        gender_mismatches: Same idea for gender.
    """

    total: int
    valid: int
    invalid: int
    duplicate_groups: int
    duplicate_rows: int
    dob_mismatches: int
    gender_mismatches: int


@dataclass(frozen=True, slots=True)
class NICBatchResult:
    """The outcome of validating a list / dataframe of NICs.

    Attributes:
        results: One :class:`NicResult` per input row, in the same
            order as the input.
        duplicates: Mapping from canonical NIC (uppercased, V/X stripped)
            to the row indices it appeared at. Only entries with two or
            more indices are included.
        summary: Roll-up counts.
        df: When the input was a pandas or polars DataFrame, this is a
            copy of that frame with helakit's per-row columns appended.
            ``None`` when the input was a list.
    """

    results: list[NicResult]
    duplicates: dict[str, list[int]] = field(default_factory=dict)
    summary: NICSummary = field(default_factory=lambda: NICSummary(0, 0, 0, 0, 0, 0, 0))
    df: Any | None = None

    def __iter__(self) -> Iterator[NicResult]:
        return iter(self.results)

    def __len__(self) -> int:
        return len(self.results)

    def __getitem__(self, index: int) -> NicResult:
        return self.results[index]

    def __bool__(self) -> bool:
        return self.summary.invalid == 0
