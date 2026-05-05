"""Old → new NIC format conversion.

The reverse direction is intentionally not supported — new NICs do not
encode the V/X voting flag, so converting back would lose information.
``convert_nic`` is idempotent on inputs that are already in the new
format: pass a 12-digit NIC and you get the same NIC back.
"""

from __future__ import annotations

from typing import Any, Literal, overload

from helakit._core.exceptions import InvalidInputError
from helakit.nic._data import DEFAULT_OLD_NIC_CENTURY, NEW_FORMAT_LENGTH
from helakit.nic._dispatch import detect_kind
from helakit.nic._normalize import normalize
from helakit.nic._parse import parse
from helakit.nic.exceptions import NICFormatError

ErrorMode = Literal["raise", "coerce", "ignore"]
_VALID_ERROR_MODES: tuple[ErrorMode, ...] = ("raise", "coerce", "ignore")


@overload
def convert_nic(value: str, *, century: int = ...) -> str: ...


@overload
def convert_nic(
    value: list[str] | tuple[str, ...],
    *,
    century: int = ...,
    errors: ErrorMode = ...,
) -> list[str | None]: ...


@overload
def convert_nic(
    value: Any,
    *,
    century: int = ...,
    nic_col: str | None = ...,
    errors: ErrorMode = ...,
    error_col: str | None = ...,
) -> Any: ...


def convert_nic(
    value: Any,
    *,
    century: int = DEFAULT_OLD_NIC_CENTURY,
    nic_col: str | None = None,
    errors: ErrorMode = "raise",
    error_col: str | None = None,
) -> Any:
    """Convert an old-format NIC to the new 12-digit format.

    Args:
        value: Either a single NIC string, a list of strings, a pandas
            or polars Series, or a pandas/polars DataFrame. For Series
            input the function returns a Series of the same length,
            preserving index/name. For DataFrame input ``nic_col``
            specifies which column to convert; the function returns a
            copy of the frame with a new ``nic_converted`` column added.
        century: Century to assume for two-digit years on old NICs.
        nic_col: Required for tabular input.
        errors: How to handle individual values that cannot be converted.
            ``"raise"`` (default) propagates :class:`NICFormatError` on
            the first bad value — same as ``pandas`` strict mode.
            ``"coerce"`` replaces bad values with ``None`` so a single
            malformed row no longer fails the whole batch. ``"ignore"``
            leaves the original input through untouched. Scalar input
            always raises regardless of this setting.
        error_col: Column name for per-row error messages (DataFrame
            input only). When supplied, the returned frame gets an extra
            column with the failure message or ``None`` for rows that
            converted cleanly. Implies ``errors="coerce"`` if ``errors``
            is left at the default of ``"raise"``.

    Returns:
        The same shape as the input — string for string, list for list,
        DataFrame for DataFrame.

    Raises:
        NICFormatError: If a value cannot be parsed (e.g. wrong length,
            non-numeric content) and ``errors="raise"``. New-format input
            passes through unchanged.
        InvalidInputError: For unsupported input types or invalid
            ``errors`` values.
    """
    if errors not in _VALID_ERROR_MODES:
        raise InvalidInputError(f"errors must be one of {_VALID_ERROR_MODES}; got {errors!r}.")

    kind = detect_kind(value)
    if kind == "str":
        if error_col is not None:
            raise InvalidInputError("error_col only applies to batch input.")
        return _convert_one(value, century=century)

    effective_errors: ErrorMode = (
        "coerce" if (error_col is not None and errors == "raise") else errors
    )

    if kind == "list_of_str":
        if error_col is not None:
            raise InvalidInputError(
                "error_col only applies to DataFrame input. For lists, inspect the "
                "returned values directly or use validate_nic for per-row diagnostics."
            )
        return [_convert_with_mode(v, century=century, errors=effective_errors)[0] for v in value]
    if kind == "pandas":
        return _convert_pandas(value, nic_col, century, effective_errors, error_col)
    if kind == "polars":
        return _convert_polars(value, nic_col, century, effective_errors, error_col)
    raise InvalidInputError(f"convert_nic does not accept input of kind {kind!r}.")


def _convert_one(value: str, *, century: int) -> str:
    cleaned = normalize(value)
    if len(cleaned) == NEW_FORMAT_LENGTH and cleaned.isdigit():
        return cleaned

    parsed, errors = parse(cleaned, century=century)
    if parsed is None or errors:
        codes = ", ".join(e.code for e in errors) or "unparseable"
        raise NICFormatError(f"Cannot convert {value!r} — input is not a valid old NIC ({codes}).")
    if parsed.format == "new":
        return cleaned

    return f"{parsed.year:04d}{parsed.raw_day_code:03d}0{parsed.serial:03d}{parsed.check_digit}"


def _convert_with_mode(
    value: Any,
    *,
    century: int,
    errors: ErrorMode,
) -> tuple[Any, str | None]:
    """Convert one value under a batch error mode.

    Returns ``(converted_value, error_message)``. For successful conversions
    the error message is ``None``; for failures the value reflects the
    chosen mode (``None`` for coerce, the original input for ignore).
    """
    if not isinstance(value, str):
        if errors == "raise":
            raise NICFormatError(
                f"Cannot convert {value!r} — expected a string, got {type(value).__name__}."
            )
        message = f"expected a string, got {type(value).__name__}"
        return (None if errors == "coerce" else value, message)

    try:
        return (_convert_one(value, century=century), None)
    except NICFormatError as exc:
        if errors == "raise":
            raise
        return (None if errors == "coerce" else value, str(exc))


def _convert_pandas(
    df: Any,
    nic_col: str | None,
    century: int,
    errors: ErrorMode,
    error_col: str | None,
) -> Any:
    import pandas as pd

    if isinstance(df, pd.Series):
        if nic_col is not None:
            raise InvalidInputError("nic_col only applies to DataFrame input, not Series.")
        if error_col is not None:
            raise InvalidInputError(
                "error_col only applies to DataFrame input. For Series, pass the "
                "Series to validate_nic for per-row diagnostics, or call convert_nic "
                "on the DataFrame with error_col instead."
            )
        converted = [_convert_with_mode(v, century=century, errors=errors)[0] for v in df.tolist()]
        return pd.Series(converted, index=df.index, name=df.name, dtype=object)
    if nic_col is None:
        raise InvalidInputError("nic_col is required when converting a DataFrame.")
    if nic_col not in df.columns:
        raise InvalidInputError(f"Column {nic_col!r} not found. Available: {sorted(df.columns)}.")
    converted_list: list[Any] = []
    error_messages: list[str | None] = []
    for raw in df[nic_col].tolist():
        value, message = _convert_with_mode(raw, century=century, errors=errors)
        converted_list.append(value)
        error_messages.append(message)
    annotated = df.copy()
    annotated["nic_converted"] = converted_list
    if error_col is not None:
        annotated[error_col] = error_messages
    return annotated


def _convert_polars(
    df: Any,
    nic_col: str | None,
    century: int,
    errors: ErrorMode,
    error_col: str | None,
) -> Any:
    import polars as pl

    if isinstance(df, pl.Series):
        if nic_col is not None:
            raise InvalidInputError("nic_col only applies to DataFrame input, not Series.")
        if error_col is not None:
            raise InvalidInputError(
                "error_col only applies to DataFrame input. For Series, pass the "
                "Series to validate_nic for per-row diagnostics, or call convert_nic "
                "on the DataFrame with error_col instead."
            )
        converted = [_convert_with_mode(v, century=century, errors=errors)[0] for v in df.to_list()]
        return pl.Series(df.name, converted, dtype=pl.Utf8)
    if nic_col is None:
        raise InvalidInputError("nic_col is required when converting a DataFrame.")
    if nic_col not in df.columns:
        raise InvalidInputError(f"Column {nic_col!r} not found. Available: {sorted(df.columns)}.")
    converted_list: list[Any] = []
    error_messages: list[str | None] = []
    for raw in df[nic_col].to_list():
        value, message = _convert_with_mode(raw, century=century, errors=errors)
        converted_list.append(value)
        error_messages.append(message)
    new_columns = [pl.Series("nic_converted", converted_list, dtype=pl.Utf8)]
    if error_col is not None:
        new_columns.append(pl.Series(error_col, error_messages, dtype=pl.Utf8))
    return df.with_columns(new_columns)
