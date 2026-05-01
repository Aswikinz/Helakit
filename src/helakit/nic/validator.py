"""Public NIC validation entry points.

:func:`validate_nic` accepts a single string, a ``list[str]``,
a ``list[dict]``, a pandas DataFrame, or a polars DataFrame. When the
input is a list-of-dicts or a DataFrame and ``dob_col`` / ``gender_col``
are supplied, each row's NIC is also cross-checked against the supplied
values and any mismatches are reported in detail.

Format / checksum validation is structural only — the Department for
Registration of Persons has not published the modulo-11 check digit
algorithm so we cannot verify it (see :mod:`helakit.nic._parse`).
"""

from __future__ import annotations

from datetime import date
from typing import Any, Literal, overload

from helakit._core.exceptions import InvalidInputError
from helakit._core.result import ValidationError, ValidationResult
from helakit.nic._data import (
    DEFAULT_OLD_NIC_CENTURY,
    NEW_FORMAT_LENGTH,
    OLD_FORMAT_LENGTH,
)
from helakit.nic._dispatch import coerce_dob, coerce_gender, detect_kind
from helakit.nic._normalize import normalize_for_dedup
from helakit.nic._parse import ParsedNIC, parse
from helakit.nic._types import NICBatchResult, NICDecoded, NICSummary

FormatHint = Literal["old", "new", "any"]


@overload
def validate_nic(
    data: str,
    *,
    format: FormatHint = ...,
    century: int = ...,
) -> ValidationResult: ...


@overload
def validate_nic(
    data: list[str] | list[dict[str, Any]] | tuple[str, ...],
    *,
    format: FormatHint = ...,
    nic_col: str | None = ...,
    dob_col: str | None = ...,
    gender_col: str | None = ...,
    century: int = ...,
) -> NICBatchResult: ...


@overload
def validate_nic(
    data: Any,
    *,
    format: FormatHint = ...,
    nic_col: str | None = ...,
    dob_col: str | None = ...,
    gender_col: str | None = ...,
    century: int = ...,
) -> NICBatchResult: ...


def validate_nic(
    data: Any,
    *,
    format: FormatHint = "any",
    nic_col: str | None = None,
    dob_col: str | None = None,
    gender_col: str | None = None,
    century: int = DEFAULT_OLD_NIC_CENTURY,
) -> ValidationResult | NICBatchResult:
    """Validate one or many Sri Lankan NIC numbers.

    Args:
        data: A single NIC string, a ``list[str]``, a ``list[dict]``, a
            pandas DataFrame, or a polars DataFrame.
        format: Restrict to ``"old"`` or ``"new"`` only. ``"any"``
            (default) accepts both.
        nic_col: Column name holding NICs (required for tabular input).
        dob_col: Column name holding dates of birth. When supplied each
            row is cross-checked and the per-row result records whether
            the decoded DOB matched.
        gender_col: Column name holding gender (``M``/``F``/``Male``/
            ``Female``, case-insensitive).
        century: Century to assume for two-digit years on old NICs.
            Defaults to ``1900``.

    Returns:
        A :class:`ValidationResult` for scalar input, or a
        :class:`NICBatchResult` for any iterable input.

    Raises:
        InvalidInputError: For unsupported input types or unparseable
            gender / DOB values.
    """
    kind = detect_kind(data)
    if kind == "str":
        return _validate_one(data, format=format, century=century)

    rows = _extract_rows(
        data,
        kind=kind,
        nic_col=nic_col,
        dob_col=dob_col,
        gender_col=gender_col,
    )
    return _validate_batch(
        rows,
        kind=kind,
        original=data,
        nic_col=nic_col,
        dob_col=dob_col,
        gender_col=gender_col,
        format=format,
        century=century,
    )


def is_valid_nic(value: str, *, format: FormatHint = "any") -> bool:
    """Return ``True`` if ``value`` is a structurally valid NIC.

    Scalar-only — for batch checks use :func:`validate_nic` and inspect
    each ``ValidationResult``.

    Raises:
        InvalidInputError: If ``value`` is not a string.
    """
    if not isinstance(value, str):
        raise InvalidInputError(f"is_valid_nic requires a string; got {type(value).__name__}.")
    return _validate_one(value, format=format).is_valid


def _validate_one(
    value: str,
    *,
    format: FormatHint,
    century: int = DEFAULT_OLD_NIC_CENTURY,
    expected_dob: date | None = None,
    expected_gender: Literal["male", "female"] | None = None,
) -> ValidationResult:
    parsed, errors = parse(value, century=century)

    format_error = _check_format_hint(parsed, format)
    if format_error is not None:
        errors = [*errors, format_error]

    decoded: NICDecoded | None = None
    if parsed is not None and parsed.dob is not None:
        decoded = NICDecoded(
            format=parsed.format,
            dob=parsed.dob,
            gender=parsed.gender,
            age=_age(parsed.dob),
            year=parsed.year,
            day_code=parsed.day_code,
            serial=parsed.serial,
            check_digit=parsed.check_digit,
            voting_eligible=parsed.voting_eligible,
        )

    data: dict[str, Any] = {}
    if decoded is not None:
        data["decoded"] = decoded
    if parsed is not None:
        data["format"] = parsed.format

    cross = _cross_check(parsed, expected_dob, expected_gender)
    if cross is not None:
        data.update(cross)

    is_valid = parsed is not None and not errors
    normalized = normalize_for_dedup(value) if parsed is not None else None

    return ValidationResult(
        is_valid=is_valid,
        value=value,
        normalized=normalized,
        errors=errors,
        data=data,
    )


def _check_format_hint(parsed: ParsedNIC | None, format: FormatHint) -> ValidationError | None:
    if format == "any" or parsed is None:
        return None
    if format == "old" and parsed.format != "old":
        return ValidationError(
            code="nic.format_mismatch",
            message=f"Expected old-format NIC ({OLD_FORMAT_LENGTH} chars); got new format.",
            field="format",
        )
    if format == "new" and parsed.format != "new":
        return ValidationError(
            code="nic.format_mismatch",
            message=f"Expected new-format NIC ({NEW_FORMAT_LENGTH} chars); got old format.",
            field="format",
        )
    return None


def _cross_check(
    parsed: ParsedNIC | None,
    expected_dob: date | None,
    expected_gender: Literal["male", "female"] | None,
) -> dict[str, Any] | None:
    if parsed is None:
        return None
    if expected_dob is None and expected_gender is None:
        return None

    extras: dict[str, Any] = {}
    reasons: list[str] = []
    detail_parts: list[str] = []

    if expected_dob is not None:
        match = parsed.dob == expected_dob
        extras["dob_match"] = match
        extras["dob_supplied"] = expected_dob
        extras["dob_decoded"] = parsed.dob
        if not match:
            reasons.append("dob")
            detail_parts.append(
                f"dob: NIC says {parsed.dob.isoformat() if parsed.dob else 'unknown'}, "
                f"supplied {expected_dob.isoformat()}"
            )

    if expected_gender is not None:
        match = parsed.gender == expected_gender
        extras["gender_match"] = match
        extras["gender_supplied"] = expected_gender
        extras["gender_decoded"] = parsed.gender
        if not match:
            reasons.append("gender")
            detail_parts.append(f"gender: NIC says {parsed.gender}, supplied {expected_gender}")

    extras["mismatch_reasons"] = reasons
    extras["mismatch_detail"] = "; ".join(detail_parts) if detail_parts else None
    return extras


def _age(dob: date, *, today: date | None = None) -> int:
    today = today or date.today()
    years = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        years -= 1
    return years


def _extract_rows(
    data: Any,
    *,
    kind: str,
    nic_col: str | None,
    dob_col: str | None,
    gender_col: str | None,
) -> list[dict[str, Any]]:
    """Normalise any batch input into a list of ``{nic, dob, gender}`` dicts."""
    if kind == "list_of_str":
        return [{"nic": v} for v in data]

    if kind == "list_of_dict":
        if nic_col is None:
            raise InvalidInputError("nic_col is required when validating a list of dicts.")
        return [
            {
                "nic": row.get(nic_col, ""),
                "dob": row.get(dob_col) if dob_col else None,
                "gender": row.get(gender_col) if gender_col else None,
            }
            for row in data
        ]

    if kind == "pandas":
        return _rows_from_pandas(data, nic_col, dob_col, gender_col)

    if kind == "polars":
        return _rows_from_polars(data, nic_col, dob_col, gender_col)

    raise InvalidInputError(f"Cannot extract rows from input of kind {kind!r}.")


def _rows_from_pandas(
    df: Any, nic_col: str | None, dob_col: str | None, gender_col: str | None
) -> list[dict[str, Any]]:
    if nic_col is None:
        raise InvalidInputError("nic_col is required when validating a DataFrame.")
    _ensure_columns(df, [nic_col, dob_col, gender_col])
    rows: list[dict[str, Any]] = []
    nic_values = df[nic_col].tolist()
    dob_values = df[dob_col].tolist() if dob_col else [None] * len(df)
    gender_values = df[gender_col].tolist() if gender_col else [None] * len(df)
    for nic, dob, gender in zip(nic_values, dob_values, gender_values, strict=True):
        rows.append({"nic": nic, "dob": dob, "gender": gender})
    return rows


def _rows_from_polars(
    df: Any, nic_col: str | None, dob_col: str | None, gender_col: str | None
) -> list[dict[str, Any]]:
    if nic_col is None:
        raise InvalidInputError("nic_col is required when validating a DataFrame.")
    _ensure_columns(df, [nic_col, dob_col, gender_col])
    nic_values = df[nic_col].to_list()
    dob_values = df[dob_col].to_list() if dob_col else [None] * df.height
    gender_values = df[gender_col].to_list() if gender_col else [None] * df.height
    return [
        {"nic": nic, "dob": dob, "gender": gender}
        for nic, dob, gender in zip(nic_values, dob_values, gender_values, strict=True)
    ]


def _ensure_columns(df: Any, names: list[str | None]) -> None:
    columns = set(df.columns)
    for name in names:
        if name is not None and name not in columns:
            raise InvalidInputError(
                f"Column {name!r} not found in DataFrame. Available columns: {sorted(columns)}."
            )


def _validate_batch(
    rows: list[dict[str, Any]],
    *,
    kind: str,
    original: Any,
    nic_col: str | None,
    dob_col: str | None,
    gender_col: str | None,
    format: FormatHint,
    century: int,
) -> NICBatchResult:
    results: list[ValidationResult] = []
    normalized_index: dict[str, list[int]] = {}
    dob_mismatches = 0
    gender_mismatches = 0

    for index, row in enumerate(rows):
        raw_nic = row["nic"]
        if not isinstance(raw_nic, str):
            results.append(
                ValidationResult(
                    is_valid=False,
                    value="" if raw_nic is None else str(raw_nic),
                    errors=[
                        ValidationError(
                            code="nic.not_a_string",
                            message=(f"Expected a string NIC; got {type(raw_nic).__name__}."),
                        )
                    ],
                )
            )
            continue

        expected_dob = coerce_dob(row.get("dob")) if dob_col else None
        expected_gender = coerce_gender(row.get("gender")) if gender_col else None

        result = _validate_one(
            raw_nic,
            format=format,
            century=century,
            expected_dob=expected_dob,
            expected_gender=expected_gender,
        )
        results.append(result)

        if result.normalized is not None:
            normalized_index.setdefault(result.normalized, []).append(index)
        if result.data.get("dob_match") is False:
            dob_mismatches += 1
        if result.data.get("gender_match") is False:
            gender_mismatches += 1

    duplicates = {key: indices for key, indices in normalized_index.items() if len(indices) > 1}
    valid_count = sum(1 for r in results if r.is_valid)
    total = len(results)
    summary = NICSummary(
        total=total,
        valid=valid_count,
        invalid=total - valid_count,
        duplicate_groups=len(duplicates),
        duplicate_rows=sum(len(v) for v in duplicates.values()),
        dob_mismatches=dob_mismatches,
        gender_mismatches=gender_mismatches,
    )

    df_with_columns: Any | None = None
    if kind == "pandas":
        df_with_columns = _annotate_pandas(original, results)
    elif kind == "polars":
        df_with_columns = _annotate_polars(original, results)

    return NICBatchResult(
        results=results,
        duplicates=duplicates,
        summary=summary,
        df=df_with_columns,
    )


def _result_columns(results: list[ValidationResult]) -> dict[str, list[Any]]:
    cols: dict[str, list[Any]] = {
        "nic_valid": [],
        "nic_normalized": [],
        "nic_format": [],
        "nic_decoded_dob": [],
        "nic_decoded_gender": [],
        "nic_dob_match": [],
        "nic_gender_match": [],
        "nic_mismatch_reasons": [],
        "nic_mismatch_detail": [],
        "nic_errors": [],
    }
    for r in results:
        decoded = r.data.get("decoded")
        cols["nic_valid"].append(r.is_valid)
        cols["nic_normalized"].append(r.normalized)
        cols["nic_format"].append(r.data.get("format"))
        cols["nic_decoded_dob"].append(decoded.dob if decoded else None)
        cols["nic_decoded_gender"].append(decoded.gender if decoded else None)
        cols["nic_dob_match"].append(r.data.get("dob_match"))
        cols["nic_gender_match"].append(r.data.get("gender_match"))
        reasons = r.data.get("mismatch_reasons") or []
        cols["nic_mismatch_reasons"].append(",".join(reasons) if reasons else None)
        cols["nic_mismatch_detail"].append(r.data.get("mismatch_detail"))
        cols["nic_errors"].append(",".join(e.code for e in r.errors) if r.errors else None)
    return cols


def _annotate_pandas(df: Any, results: list[ValidationResult]) -> Any:
    cols = _result_columns(results)
    annotated = df.copy()
    for name, values in cols.items():
        annotated[name] = values
    return annotated


def _annotate_polars(df: Any, results: list[ValidationResult]) -> Any:
    import polars as pl

    cols = _result_columns(results)
    return df.with_columns([pl.Series(name, values) for name, values in cols.items()])
