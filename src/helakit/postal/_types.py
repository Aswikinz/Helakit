"""Public dataclasses returned by the postal-code validator."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from typing import Any, overload

from helakit._core import frames
from helakit._core.result import ValidationResult


@dataclass(frozen=True, slots=True)
class PostalDecoded:
    """Structured metadata about a recognised Sri Lankan postal code.

    Returned in ``PostalResult.data["decoded"]`` and accessible as
    ``PostalResult.decoded``.

    Attributes:
        post_office: Name of the post office the code names, as published
            by the Department of Posts (e.g. ``"Nugegoda"``).
        district: District the post office sits in (e.g. ``"Colombo"``).
        province: Province the district belongs to (e.g. ``"Western"``).
        district_code: Short district code (e.g. ``"CMB"``), a key into
            ``helakit._data.districts.DISTRICTS``.
        province_code: Short province code (e.g. ``"WP"``).
        sub_post: ``True`` when the code names a sub post office rather
            than a main post office.
    """

    post_office: str
    district: str
    province: str
    district_code: str
    province_code: str
    sub_post: bool


class PostalResult(ValidationResult):
    """Validation result returned by :func:`~helakit.postal.validate_postal`.

    Adds typed property accessors for every field the postal validator
    extracts, including pass-through accessors that reach into
    :class:`PostalDecoded`::

        result.decoded.district   # works
        result.district           # also works — same value

    Properties return ``None`` on invalid results so attribute access never
    raises — guard with ``if result:`` before reading.
    """

    __slots__ = ()

    @property
    def decoded(self) -> PostalDecoded | None:
        """Full :class:`PostalDecoded` payload. ``None`` if invalid."""
        return self.data.get("decoded")

    @property
    def post_office(self) -> str | None:
        """Post office name. ``None`` if invalid."""
        return self.data.get("post_office")

    @property
    def district(self) -> str | None:
        """District name. ``None`` if invalid."""
        return self.data.get("district")

    @property
    def province(self) -> str | None:
        """Province name. ``None`` if invalid."""
        return self.data.get("province")

    @property
    def district_code(self) -> str | None:
        """Short district code (e.g. ``"CMB"``). ``None`` if invalid."""
        return self.data.get("district_code")

    @property
    def province_code(self) -> str | None:
        """Short province code (e.g. ``"WP"``). ``None`` if invalid."""
        return self.data.get("province_code")

    @property
    def sub_post(self) -> bool | None:
        """``True`` for a sub post office. ``None`` if invalid."""
        return self.data.get("sub_post")

    # --- Cross-check results (only populated when district_col is supplied
    #     in batch mode) ------------------------------------------------------

    @property
    def district_match(self) -> bool | None:
        """``True`` / ``False`` if a district was cross-checked; ``None``
        otherwise."""
        return self.data.get("district_match")

    @property
    def mismatch_reasons(self) -> list[str] | None:
        """Which cross-check fields disagreed with the code. ``None`` when no
        cross-check ran."""
        return self.data.get("mismatch_reasons")

    @property
    def mismatch_detail(self) -> str | None:
        """Human-readable diff of cross-check vs decoded. ``None`` when no
        cross-check ran or everything matched."""
        return self.data.get("mismatch_detail")

    _RECORD_FIELDS: tuple[str, ...] = (
        "postal",
        "postal_valid",
        "postal_normalized",
        "postal_post_office",
        "postal_district",
        "postal_province",
        "postal_sub_post",
        "postal_district_match",
        "postal_mismatch_detail",
        "postal_errors",
    )

    @classmethod
    def record_fields(cls) -> tuple[str, ...]:
        """Names of the keys :meth:`to_dict` emits, in column order."""
        return cls._RECORD_FIELDS

    def to_dict(self) -> dict[str, Any]:
        """Flatten this result into one plain, column-per-field dict.

        The keys match the diagnostic columns that
        :meth:`PostalBatchResult.to_pandas` produces, so one row of that
        frame and ``result.to_dict()`` look identical.

        Example:
            >>> validate_postal("10250").to_dict()["postal_post_office"]
            'Nugegoda'
        """
        return {
            "postal": self.value,
            "postal_valid": self.is_valid,
            "postal_normalized": self.normalized,
            "postal_post_office": self.post_office,
            "postal_district": self.district,
            "postal_province": self.province,
            "postal_sub_post": self.sub_post,
            "postal_district_match": self.district_match,
            "postal_mismatch_detail": self.mismatch_detail,
            "postal_errors": ",".join(e.code for e in self.errors) if self.errors else None,
        }


@dataclass(frozen=True, slots=True)
class PostalSummary:
    """Aggregate counts for a batch validation run.

    Attributes:
        total: Number of input rows processed.
        valid: Rows whose code was recognised.
        invalid: Rows that failed validation.
        duplicate_groups: Number of distinct codes appearing in more than
            one row.
        duplicate_rows: Total rows participating in any duplicate group.
        district_mismatches: Rows where the supplied district differed from
            the district the code belongs to (only counted when both were
            available).
    """

    total: int
    valid: int
    invalid: int
    duplicate_groups: int
    duplicate_rows: int
    district_mismatches: int

    def to_dict(self) -> dict[str, int]:
        """Return the counts as a plain dict.

        Useful for turning the summary into a pandas object::

            pd.Series(batch.describe().to_dict())
        """
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PostalBatchResult:
    """The outcome of validating a list / Series / DataFrame of postal codes.

    Behaves like a familiar pandas-style container: it has a length, iterates
    over its rows, supports integer *and* slice indexing, and converts to
    tabular form via :meth:`to_pandas` / :meth:`to_polars` / :meth:`to_dicts`
    regardless of what shape the input was.

    Attributes:
        results: One :class:`PostalResult` per input row, in input order.
        duplicates: Mapping from canonical code to the row indices it
            appeared at. Only entries with two or more indices are included.
        summary: Roll-up counts. Also reachable via :meth:`describe`.
        df: When the input was a pandas or polars DataFrame, this is a copy
            of that frame with helakit's per-row columns appended. ``None``
            for list and Series input — use :meth:`to_pandas` or
            :meth:`to_polars` there.
    """

    results: list[PostalResult]
    duplicates: dict[str, list[int]] = field(default_factory=dict)
    summary: PostalSummary = field(default_factory=lambda: PostalSummary(0, 0, 0, 0, 0, 0))
    df: Any | None = None

    def __iter__(self) -> Iterator[PostalResult]:
        return iter(self.results)

    def __len__(self) -> int:
        return len(self.results)

    @overload
    def __getitem__(self, index: int) -> PostalResult: ...

    @overload
    def __getitem__(self, index: slice) -> list[PostalResult]: ...

    def __getitem__(self, index: int | slice) -> PostalResult | list[PostalResult]:
        """Integer indexing returns one result; slices return a list.

        Example:
            >>> batch[0]      # first PostalResult
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

            df[batch.is_valid]                    # rows with valid codes
            df[[not v for v in batch.is_valid]]   # the offenders
        """
        return [r.is_valid for r in self.results]

    @property
    def valid(self) -> list[PostalResult]:
        """Only the rows that validated cleanly (order preserved)."""
        return [r for r in self.results if r.is_valid]

    @property
    def invalid(self) -> list[PostalResult]:
        """Only the rows that failed validation (order preserved)."""
        return [r for r in self.results if not r.is_valid]

    def head(self, n: int = 5) -> list[PostalResult]:
        """First ``n`` results, mirroring ``DataFrame.head``."""
        return self.results[:n]

    def describe(self) -> PostalSummary:
        """Aggregate counts, mirroring ``DataFrame.describe``.

        Returns the same object as :attr:`summary`; call
        ``batch.describe().to_dict()`` for a plain dict.
        """
        return self.summary

    def to_dicts(self) -> list[dict[str, Any]]:
        """One flat record dict per row (polars-style ``to_dicts``).

        Needs no optional dependencies. The keys are the ``postal_*``
        diagnostic columns documented on :meth:`to_pandas`, plus ``postal``
        holding the original input value.
        """
        return [r.to_dict() for r in self.results]

    def to_pandas(self) -> Any:
        """Return the batch as a pandas DataFrame.

        When the input was already a pandas DataFrame this returns
        :attr:`df` (the input copy with diagnostic columns appended). For
        every other input shape — list, list-of-dicts, Series, polars frame
        — a fresh frame is built with one row per input and the ``postal_*``
        diagnostic columns.

        Raises:
            InvalidInputError: If pandas is not installed. Install it with
                ``pip install helakit[pandas]``.
        """
        if frames.frame_library(self.df) == "pandas":
            return self.df
        return frames.build_pandas(self.to_dicts())

    def to_polars(self) -> Any:
        """Return the batch as a polars DataFrame.

        Mirrors :meth:`to_pandas`: returns :attr:`df` when the input was a
        polars DataFrame, otherwise builds a fresh frame from
        :meth:`to_dicts`.

        Raises:
            InvalidInputError: If polars is not installed. Install it with
                ``pip install helakit[polars]``.
        """
        if frames.frame_library(self.df) == "polars":
            return self.df
        return frames.build_polars(self.to_dicts())
