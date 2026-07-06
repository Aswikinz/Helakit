"""Public dataclasses returned by the NIC validator."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any, Literal, overload

from helakit._core.exceptions import InvalidInputError
from helakit._core.result import ValidationResult


@dataclass(frozen=True, slots=True)
class NICDecoded:
    """Structured fields extracted from a valid NIC.

    Age is intentionally *not* a stored field: it depends on the current
    date, which the NIC does not encode. Read it through :meth:`age_at`
    (deterministic — pass the reference date) or the :attr:`age` property
    (convenience — computed against today on each access).

    Attributes:
        format: Either ``"old"`` (9 digits + V/X) or ``"new"`` (12 digits).
        dob: Decoded date of birth.
        gender: Either ``"male"`` or ``"female"``, derived from the
            day-of-year encoding.
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
    year: int
    day_code: int
    serial: int
    check_digit: int
    voting_eligible: bool | None

    def age_at(self, today: date | None = None) -> int:
        """Completed years between :attr:`dob` and ``today``.

        Args:
            today: The reference date to measure age against. Defaults to
                :func:`datetime.date.today` when omitted — pass an explicit
                date for deterministic, testable results.

        Example:
            >>> from datetime import date
            >>> decoded.age_at(date(2026, 1, 1))
            43
        """
        ref = today or date.today()
        years = ref.year - self.dob.year
        if (ref.month, ref.day) < (self.dob.month, self.dob.day):
            years -= 1
        return years

    @property
    def age(self) -> int:
        """Completed years as of today.

        Recomputed on every access (against the current date), so it never
        goes stale. For a fixed reference date, use :meth:`age_at`.
        """
        return self.age_at()


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
        """Completed years as of today, recomputed on access. ``None`` if
        invalid. For a fixed reference date, use :meth:`age_at`."""
        decoded = self.decoded
        return decoded.age if decoded else None

    def age_at(self, today: date | None = None) -> int | None:
        """Completed years between the decoded DOB and ``today``.

        Deterministic counterpart to :attr:`age` — pass an explicit
        reference date. Returns ``None`` on invalid results.
        """
        decoded = self.decoded
        return decoded.age_at(today) if decoded else None

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

    _RECORD_FIELDS: tuple[str, ...] = (
        "nic",
        "nic_valid",
        "nic_normalized",
        "nic_format",
        "nic_decoded_dob",
        "nic_decoded_gender",
        "nic_dob_match",
        "nic_gender_match",
        "nic_mismatch_reasons",
        "nic_mismatch_detail",
        "nic_errors",
    )

    @classmethod
    def record_fields(cls) -> tuple[str, ...]:
        """Names of the keys :meth:`to_dict` emits, in column order."""
        return cls._RECORD_FIELDS

    def to_dict(self) -> dict[str, Any]:
        """Flatten this result into one plain, column-per-field dict.

        The keys match the diagnostic columns that
        :meth:`NICBatchResult.to_pandas` produces, so one row of that
        frame and ``result.to_dict()`` look identical. Handy for feeding
        a single result into ``pd.DataFrame([result.to_dict()])`` or a
        JSON serialiser.

        Example:
            >>> validate_nic("820149894V").to_dict()
            {'nic': '820149894V', 'nic_valid': True, 'nic_normalized': '820149894', ...}
        """
        reasons = self.mismatch_reasons or []
        return {
            "nic": self.value,
            "nic_valid": self.is_valid,
            "nic_normalized": self.normalized,
            "nic_format": self.format,
            "nic_decoded_dob": self.dob,
            "nic_decoded_gender": self.gender,
            "nic_dob_match": self.dob_match,
            "nic_gender_match": self.gender_match,
            "nic_mismatch_reasons": ",".join(reasons) if reasons else None,
            "nic_mismatch_detail": self.mismatch_detail,
            "nic_errors": ",".join(e.code for e in self.errors) if self.errors else None,
        }


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

    def to_dict(self) -> dict[str, int]:
        """Return the counts as a plain dict.

        Useful for turning the summary into a pandas object::

            pd.Series(batch.describe().to_dict())
        """
        return asdict(self)


@dataclass(frozen=True, slots=True)
class NICBatchResult:
    """The outcome of validating a list / Series / DataFrame of NICs.

    Behaves like a familiar pandas-style container: it has a length,
    iterates over its rows, supports integer *and* slice indexing, and
    converts to tabular form via :meth:`to_pandas` / :meth:`to_polars` /
    :meth:`to_dicts` regardless of what shape the input was.

    Attributes:
        results: One :class:`NicResult` per input row, in the same
            order as the input.
        duplicates: Mapping from canonical NIC (uppercased, V/X stripped)
            to the row indices it appeared at. Only entries with two or
            more indices are included.
        summary: Roll-up counts. Also reachable via :meth:`describe`.
        df: When the input was a pandas or polars DataFrame, this is a
            copy of that frame with helakit's per-row columns appended.
            ``None`` for list and Series input — use :meth:`to_pandas`
            or :meth:`to_polars` there.
    """

    results: list[NicResult]
    duplicates: dict[str, list[int]] = field(default_factory=dict)
    summary: NICSummary = field(default_factory=lambda: NICSummary(0, 0, 0, 0, 0, 0, 0))
    df: Any | None = None

    def __iter__(self) -> Iterator[NicResult]:
        return iter(self.results)

    def __len__(self) -> int:
        return len(self.results)

    @overload
    def __getitem__(self, index: int) -> NicResult: ...

    @overload
    def __getitem__(self, index: slice) -> list[NicResult]: ...

    def __getitem__(self, index: int | slice) -> NicResult | list[NicResult]:
        """Integer indexing returns one result; slices return a list.

        Example:
            >>> batch[0]      # first NicResult
            >>> batch[:3]     # first three, like df[:3]
        """
        return self.results[index]

    def __bool__(self) -> bool:
        """``True`` only when *every* row validated cleanly."""
        return self.summary.invalid == 0

    def __repr__(self) -> str:
        s = self.summary
        return (
            f"{type(self).__name__}(total={s.total}, valid={s.valid}, "
            f"invalid={s.invalid}, duplicate_groups={s.duplicate_groups})"
        )

    # --- pandas-style accessors ---------------------------------------------

    @property
    def is_valid(self) -> list[bool]:
        """Row-aligned boolean mask, like a boolean Series.

        Drops straight into pandas/polars filtering::

            df[batch.is_valid]           # keep only rows with valid NICs
            df[[not v for v in batch.is_valid]]  # the offenders
        """
        return [r.is_valid for r in self.results]

    @property
    def valid(self) -> list[NicResult]:
        """Only the rows that validated cleanly (order preserved)."""
        return [r for r in self.results if r.is_valid]

    @property
    def invalid(self) -> list[NicResult]:
        """Only the rows that failed validation (order preserved)."""
        return [r for r in self.results if not r.is_valid]

    def head(self, n: int = 5) -> list[NicResult]:
        """First ``n`` results, mirroring ``DataFrame.head``."""
        return self.results[:n]

    def describe(self) -> NICSummary:
        """Aggregate counts, mirroring ``DataFrame.describe``.

        Returns the same object as :attr:`summary`; call
        ``batch.describe().to_dict()`` for a plain dict.
        """
        return self.summary

    def to_dicts(self) -> list[dict[str, Any]]:
        """One flat record dict per row (polars-style ``to_dicts``).

        Needs no optional dependencies. The keys are the same
        ``nic_*`` diagnostic columns documented on :meth:`to_pandas`,
        plus ``nic`` holding the original input value.
        """
        return [r.to_dict() for r in self.results]

    def to_pandas(self) -> Any:
        """Return the batch as a pandas DataFrame.

        When the input was already a pandas DataFrame this returns
        :attr:`df` (the input copy with diagnostic columns appended).
        For every other input shape — list, list-of-dicts, Series,
        polars frame — a fresh frame is built with one row per input
        and the ``nic_*`` diagnostic columns.

        Raises:
            InvalidInputError: If pandas is not installed. Install it
                with ``pip install helakit[pandas]``.
        """
        try:
            import pandas as pd  # type: ignore[import-untyped]
        except ImportError as exc:  # pragma: no cover - depends on env
            raise InvalidInputError(
                "to_pandas() requires pandas. Install it with `pip install helakit[pandas]`."
            ) from exc
        if self.df is not None and type(self.df).__module__.split(".", 1)[0] == "pandas":
            return self.df
        return pd.DataFrame(self.to_dicts())

    def to_polars(self) -> Any:
        """Return the batch as a polars DataFrame.

        Mirrors :meth:`to_pandas`: returns :attr:`df` when the input was
        a polars DataFrame, otherwise builds a fresh frame from
        :meth:`to_dicts`.

        Raises:
            InvalidInputError: If polars is not installed. Install it
                with ``pip install helakit[polars]``.
        """
        try:
            import polars as pl
        except ImportError as exc:  # pragma: no cover - depends on env
            raise InvalidInputError(
                "to_polars() requires polars. Install it with `pip install helakit[polars]`."
            ) from exc
        if self.df is not None and type(self.df).__module__.split(".", 1)[0] == "polars":
            return self.df
        return pl.DataFrame(self.to_dicts())
