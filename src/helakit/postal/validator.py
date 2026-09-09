"""Postal-code validation for Sri Lankan five-digit codes.

Every code in the Department of Posts directory is resolved to the post office
it names, the district that post office sits in, and the province the district
belongs to. Like :func:`~helakit.nic.validate_nic`, the entry point accepts a
single string or a whole column — list, list of dicts, pandas/polars Series, or
pandas/polars DataFrame — and returns a batch result that behaves like a
pandas container.
"""

from __future__ import annotations

import re
from typing import Any, Literal, overload

from helakit._core import frames
from helakit._core.dispatch import detect_kind, is_na
from helakit._core.exceptions import InvalidInputError
from helakit._core.result import ValidationError
from helakit._data.districts import DISTRICT_PROVINCE, DISTRICTS
from helakit._data.provinces import PROVINCES
from helakit.postal._data import POSTAL_CODE_LENGTH, POSTAL_CODES
from helakit.postal._types import (
    PostalBatchResult,
    PostalDecoded,
    PostalResult,
    PostalSummary,
)

BatchErrorMode = Literal["raise", "coerce"]

_VALID_BATCH_ERROR_MODES: tuple[str, ...] = ("raise", "coerce")
_DIGITS_RE = re.compile(r"^[0-9]+$")
_SEPARATORS_RE = re.compile(r"[\s\-]")

# Accept a district as either its short code ("CMB") or its name ("Colombo"),
# in any letter case.
_DISTRICT_TOKENS: dict[str, str] = {
    **{code.lower(): code for code in DISTRICTS},
    **{name.lower(): code for code, name in DISTRICTS.items()},
}


@overload
def validate_postal(data: str) -> PostalResult: ...


@overload
def validate_postal(
    data: list[str] | list[dict[str, Any]] | tuple[str, ...],
    *,
    postal_col: str | None = ...,
    district_col: str | None = ...,
    errors: BatchErrorMode = ...,
) -> PostalBatchResult: ...


@overload
def validate_postal(
    data: Any,
    *,
    postal_col: str | None = ...,
    district_col: str | None = ...,
    errors: BatchErrorMode = ...,
) -> PostalBatchResult: ...


def validate_postal(
    data: Any,
    *,
    postal_col: str | None = None,
    district_col: str | None = None,
    errors: BatchErrorMode = "raise",
) -> PostalResult | PostalBatchResult:
    """Validate one or many Sri Lankan postal codes.

    Args:
        data: A single postal code string, a ``list[str]``, a ``list[dict]``,
            a pandas/polars Series, or a pandas/polars DataFrame. A Series is
            treated like a list of strings — ``postal_col`` and friends do not
            apply (a Series has no columns).
        postal_col: Column name holding postal codes. Required for DataFrame
            and list-of-dicts input; not accepted for Series input.
        district_col: Column name holding a district (short code or name, any
            letter case). When supplied each row is cross-checked and the
            per-row result records whether the district matched.
        errors: Batch-only. ``"raise"`` (default) propagates
            :class:`~helakit.InvalidInputError` if any cross-check district
            value is unparseable, matching strict pandas semantics.
            ``"coerce"`` records the failure as a per-row error instead, so a
            single malformed row no longer aborts the whole batch.

    Returns:
        A :class:`~helakit.postal.PostalResult` for scalar input, or a
        :class:`~helakit.postal.PostalBatchResult` for any iterable input.

        When valid, ``normalized`` holds the canonical five-digit string and
        these typed properties are populated:

        - ``post_office`` — post office the code names (e.g. ``"Nugegoda"``).
        - ``district`` / ``district_code`` — e.g. ``"Colombo"`` / ``"CMB"``.
        - ``province`` / ``province_code`` — e.g. ``"Western"`` / ``"WP"``.
        - ``sub_post`` — ``True`` for a sub post office.
        - ``decoded`` — a :class:`~helakit.postal.PostalDecoded` bundle.

    Raises:
        InvalidInputError: For unsupported input types, an invalid ``errors``
            value, or unparseable district values when ``errors="raise"``.
            Passing a non-string scalar is a programmer error, not bad data.

    Error codes:
        - ``postal.invalid_characters`` — input contains something other than
          ASCII digits (separators and surrounding whitespace are stripped
          first).
        - ``postal.invalid_length`` — all digits, but not exactly five of them.
        - ``postal.unknown_code`` — five digits that are not in the Department
          of Posts directory.
        - ``postal.not_a_string`` — batch-only; the row's value was not a
          string.
        - ``postal.bad_district_input`` — batch-only, ``errors="coerce"``; the
          cross-check district value could not be parsed.

    Example:
        Basic validation::

            >>> result = validate_postal("10250")
            >>> result.is_valid
            True
            >>> result.post_office
            'Nugegoda'
            >>> result.district
            'Colombo'
            >>> result.province
            'Western'

        Formatting tolerance::

            >>> validate_postal("  10250 ").normalized
            '10250'

        Handling invalid input::

            >>> result = validate_postal("99999")
            >>> result.is_valid
            False
            >>> result.errors[0].code
            'postal.unknown_code'

        A whole column::

            >>> batch = validate_postal(["10250", "80000", "99999"])
            >>> batch.is_valid
            [True, True, False]
            >>> batch.describe().valid
            2
    """
    if errors not in _VALID_BATCH_ERROR_MODES:
        raise InvalidInputError(
            f"errors must be one of {_VALID_BATCH_ERROR_MODES}; got {errors!r}."
        )

    kind = detect_kind(data)
    if kind == "str":
        return _validate_one(data)

    rows = frames.extract_rows(
        data,
        kind=kind,
        columns={"postal": postal_col, "district": district_col},
        primary="postal",
    )
    return _validate_batch(rows, kind=kind, original=data, errors=errors)


def is_valid_postal(value: str) -> bool:
    """Return ``True`` if ``value`` is a valid Sri Lankan postal code.

    Boolean shorthand for :func:`validate_postal`. Use this when you only need
    a yes/no answer; use :func:`validate_postal` when you also need the post
    office, district, or province.

    Args:
        value: The postal code to check.

    Returns:
        ``True`` when the code is in the directory, ``False`` otherwise.

    Raises:
        InvalidInputError: If ``value`` is not a string.

    Example:
        >>> is_valid_postal("10250")
        True
        >>> is_valid_postal("99999")
        False
    """
    return _validate_one(value).is_valid


# ---------------------------------------------------------------------------
# Single-value validation
# ---------------------------------------------------------------------------


def _validate_one(value: Any) -> PostalResult:
    if not isinstance(value, str):
        raise InvalidInputError(f"validate_postal requires a string; got {type(value).__name__}.")

    cleaned = _SEPARATORS_RE.sub("", value)

    if not cleaned or not _DIGITS_RE.match(cleaned):
        return PostalResult(
            is_valid=False,
            value=value,
            errors=[
                ValidationError(
                    code="postal.invalid_characters",
                    message="Postal codes must contain ASCII digits only.",
                    field="value",
                )
            ],
        )

    if len(cleaned) != POSTAL_CODE_LENGTH:
        return PostalResult(
            is_valid=False,
            value=value,
            errors=[
                ValidationError(
                    code="postal.invalid_length",
                    message=(
                        f"Sri Lankan postal codes are {POSTAL_CODE_LENGTH} digits; "
                        f"got {len(cleaned)}. Codes below 10000 keep their leading "
                        "zeros (Colombo 07 is '00700', not '700')."
                    ),
                    field="value",
                )
            ],
        )

    entry = POSTAL_CODES.get(cleaned)
    if entry is None:
        return PostalResult(
            is_valid=False,
            value=value,
            errors=[
                ValidationError(
                    code="postal.unknown_code",
                    message=(
                        f"'{cleaned}' is not a postal code in the Department of Posts directory."
                    ),
                    field="value",
                )
            ],
        )

    province_code = DISTRICT_PROVINCE[entry.district]
    decoded = PostalDecoded(
        post_office=entry.post_office,
        district=DISTRICTS[entry.district],
        province=PROVINCES[province_code],
        district_code=entry.district,
        province_code=province_code,
        sub_post=entry.sub_post,
    )
    return PostalResult(
        is_valid=True,
        value=value,
        normalized=cleaned,
        data={
            "decoded": decoded,
            "post_office": decoded.post_office,
            "district": decoded.district,
            "province": decoded.province,
            "district_code": decoded.district_code,
            "province_code": decoded.province_code,
            "sub_post": decoded.sub_post,
        },
    )


def coerce_district(value: Any) -> str | None:
    """Normalise an arbitrary district input to a short district code.

    Accepts either the short code (``"CMB"``) or the district name
    (``"Colombo"``), in any letter case. Treats ``None`` and pandas/polars NA
    sentinels as "no value supplied".

    Raises:
        InvalidInputError: For anything else.
    """
    if is_na(value):
        return None
    if not isinstance(value, str):
        raise InvalidInputError(
            f"District must be a string (code or name); got {type(value).__name__}."
        )
    token = value.strip().lower()
    code = _DISTRICT_TOKENS.get(token)
    if code is None:
        raise InvalidInputError(
            f"Unrecognised district value {value!r}. Expected a Sri Lankan district "
            "name or short code."
        )
    return code


# ---------------------------------------------------------------------------
# Batch validation
# ---------------------------------------------------------------------------


def _cross_check(decoded: PostalDecoded, expected_district: str | None) -> dict[str, Any] | None:
    if expected_district is None:
        return None
    matched = expected_district == decoded.district_code
    extra: dict[str, Any] = {
        "district_match": matched,
        "district_supplied": DISTRICTS[expected_district],
        "district_decoded": decoded.district,
        "mismatch_reasons": [] if matched else ["district"],
    }
    if not matched:
        extra["mismatch_detail"] = (
            f"district: supplied {DISTRICTS[expected_district]!r}, code says {decoded.district!r}"
        )
    return extra


def _validate_batch(
    rows: list[dict[str, Any]],
    *,
    kind: str,
    original: Any,
    errors: BatchErrorMode,
) -> PostalBatchResult:
    results: list[PostalResult] = []
    normalized_index: dict[str, list[int]] = {}
    district_mismatches = 0

    for index, row in enumerate(rows):
        raw = row.get("postal")
        if not isinstance(raw, str):
            results.append(
                PostalResult(
                    is_valid=False,
                    value="" if is_na(raw) else str(raw),
                    errors=[
                        ValidationError(
                            code="postal.not_a_string",
                            message=(f"Postal code must be a string; got {type(raw).__name__}."),
                            field="value",
                        )
                    ],
                )
            )
            continue

        result = _validate_one(raw)

        expected_district: str | None = None
        row_errors: list[ValidationError] = []
        try:
            expected_district = coerce_district(row.get("district"))
        except InvalidInputError:
            if errors == "raise":
                raise
            row_errors.append(
                ValidationError(
                    code="postal.bad_district_input",
                    message=f"Could not interpret district value {row.get('district')!r}.",
                    field="district",
                )
            )

        extra = _cross_check(result.decoded, expected_district) if result.decoded else None
        if extra is not None and extra["district_match"] is False:
            district_mismatches += 1

        if extra or row_errors:
            result = PostalResult(
                is_valid=result.is_valid and not row_errors,
                value=result.value,
                normalized=result.normalized,
                errors=[*result.errors, *row_errors],
                data={**result.data, **(extra or {})},
            )

        if result.normalized is not None:
            normalized_index.setdefault(result.normalized, []).append(index)
        results.append(result)

    duplicates = {code: idx for code, idx in normalized_index.items() if len(idx) > 1}
    valid = sum(1 for r in results if r.is_valid)
    summary = PostalSummary(
        total=len(results),
        valid=valid,
        invalid=len(results) - valid,
        duplicate_groups=len(duplicates),
        duplicate_rows=sum(len(idx) for idx in duplicates.values()),
        district_mismatches=district_mismatches,
    )

    df_with_columns = None
    if kind in ("pandas", "polars"):
        records = [r.to_dict() for r in results]
        names = [key for key in PostalResult.record_fields() if key != "postal"]
        columns = frames.result_columns(records, names)
        df_with_columns = (
            frames.annotate_pandas(original, columns)
            if kind == "pandas"
            else frames.annotate_polars(original, columns)
        )

    return PostalBatchResult(
        results=results,
        duplicates=duplicates,
        summary=summary,
        df=df_with_columns,
    )
