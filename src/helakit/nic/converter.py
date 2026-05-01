"""Old → new NIC format conversion.

The reverse direction is intentionally not supported — new NICs do not
encode the V/X voting flag, so converting back would lose information.
``convert_nic`` is idempotent on inputs that are already in the new
format: pass a 12-digit NIC and you get the same NIC back.
"""

from __future__ import annotations

from typing import Any, overload

from helakit._core.exceptions import InvalidInputError
from helakit.nic._data import DEFAULT_OLD_NIC_CENTURY, NEW_FORMAT_LENGTH
from helakit.nic._dispatch import detect_kind
from helakit.nic._normalize import normalize
from helakit.nic._parse import parse
from helakit.nic.exceptions import NICFormatError


@overload
def convert_nic(value: str, *, century: int = ...) -> str: ...


@overload
def convert_nic(value: list[str] | tuple[str, ...], *, century: int = ...) -> list[str]: ...


@overload
def convert_nic(value: Any, *, century: int = ..., nic_col: str | None = ...) -> Any: ...


def convert_nic(
    value: Any,
    *,
    century: int = DEFAULT_OLD_NIC_CENTURY,
    nic_col: str | None = None,
) -> Any:
    """Convert an old-format NIC to the new 12-digit format.

    Args:
        value: Either a single NIC string, a list of strings, a pandas
            DataFrame or a polars DataFrame. For tabular input, ``nic_col``
            specifies which column to convert; the function returns a
            copy of the frame with a new ``nic_converted`` column added.
        century: Century to assume for two-digit years on old NICs.
        nic_col: Required for tabular input.

    Returns:
        The same shape as the input — string for string, list for list,
        DataFrame for DataFrame.

    Raises:
        NICFormatError: If a value cannot be parsed (e.g. wrong length,
            non-numeric content). New-format input passes through
            unchanged.
        InvalidInputError: For unsupported input types.
    """
    kind = detect_kind(value)
    if kind == "str":
        return _convert_one(value, century=century)
    if kind == "list_of_str":
        return [_convert_one(v, century=century) for v in value]
    if kind == "pandas":
        return _convert_pandas(value, nic_col, century)
    if kind == "polars":
        return _convert_polars(value, nic_col, century)
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


def _convert_pandas(df: Any, nic_col: str | None, century: int) -> Any:
    if nic_col is None:
        raise InvalidInputError("nic_col is required when converting a DataFrame.")
    if nic_col not in df.columns:
        raise InvalidInputError(f"Column {nic_col!r} not found. Available: {sorted(df.columns)}.")
    annotated = df.copy()
    annotated["nic_converted"] = [_convert_one(v, century=century) for v in df[nic_col].tolist()]
    return annotated


def _convert_polars(df: Any, nic_col: str | None, century: int) -> Any:
    if nic_col is None:
        raise InvalidInputError("nic_col is required when converting a DataFrame.")
    if nic_col not in df.columns:
        raise InvalidInputError(f"Column {nic_col!r} not found. Available: {sorted(df.columns)}.")
    import polars as pl

    converted = [_convert_one(v, century=century) for v in df[nic_col].to_list()]
    return df.with_columns(pl.Series("nic_converted", converted))
