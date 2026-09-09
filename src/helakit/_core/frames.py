"""DataFrame plumbing shared by the batch-capable validators.

Nothing here knows about NICs or postal codes. The helpers take a mapping of
*logical* field name (``"postal"``, ``"district"``) to the caller's own column
name, so each domain supplies its own vocabulary and gets the same list /
list-of-dict / Series / DataFrame handling.

pandas and polars are imported lazily inside the functions that need them, so
importing helakit never pulls either in.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from helakit._core.exceptions import InvalidInputError


def ensure_columns(df: Any, names: Iterable[str | None]) -> None:
    """Raise if any requested column is missing from ``df``.

    Works for pandas and polars alike — both expose ``.columns``.

    Raises:
        InvalidInputError: Naming the missing column and listing what is
            available, so the caller can fix the typo without guessing.
    """
    columns = set(df.columns)
    for name in names:
        if name is not None and name not in columns:
            raise InvalidInputError(
                f"Column {name!r} not found in DataFrame. Available columns: {sorted(columns)}."
            )


def extract_rows(
    data: Any,
    *,
    kind: str,
    columns: Mapping[str, str | None],
    primary: str,
) -> list[dict[str, Any]]:
    """Normalise any batch input into a list of row dicts.

    Args:
        data: The batch input, already classified by
            :func:`~helakit._core.dispatch.detect_kind`.
        kind: The classification returned by ``detect_kind``.
        columns: Logical field name -> the caller's column name. A value of
            ``None`` means the caller did not supply that column.
        primary: The logical field holding the value being validated. Its
            column name is required for dict and DataFrame input.

    Returns:
        One dict per input row, keyed by the *logical* names in ``columns``.

    Raises:
        InvalidInputError: For a missing required column, for column names
            passed alongside Series input, or for an unhandled ``kind``.
    """
    primary_col = columns[primary]
    optional = {name: col for name, col in columns.items() if name != primary}

    if kind == "list_of_str":
        return [{primary: value} for value in data]

    if kind in ("pandas_series", "polars_series"):
        for name, col in columns.items():
            if col is not None:
                raise InvalidInputError(
                    f"{name}_col does not apply to Series input — a Series has no columns. "
                    "Pass the whole DataFrame to use column names."
                )
        values = data.tolist() if kind == "pandas_series" else data.to_list()
        return [{primary: value} for value in values]

    if kind == "list_of_dict":
        if primary_col is None:
            raise InvalidInputError(f"{primary}_col is required when validating a list of dicts.")
        return [
            {
                primary: row.get(primary_col, ""),
                **{name: (row.get(col) if col else None) for name, col in optional.items()},
            }
            for row in data
        ]

    if kind in ("pandas", "polars"):
        if primary_col is None:
            raise InvalidInputError(f"{primary}_col is required when validating a DataFrame.")
        ensure_columns(df=data, names=columns.values())
        return _rows_from_frame(data, kind=kind, columns=columns)

    raise InvalidInputError(f"Cannot extract rows from input of kind {kind!r}.")


def _rows_from_frame(
    df: Any,
    *,
    kind: str,
    columns: Mapping[str, str | None],
) -> list[dict[str, Any]]:
    height = len(df) if kind == "pandas" else df.height

    def values_for(col: str | None) -> list[Any]:
        if col is None:
            return [None] * height
        series = df[col]
        values: list[Any] = series.tolist() if kind == "pandas" else series.to_list()
        return values

    names = list(columns)
    series_values = [values_for(columns[name]) for name in names]
    return [
        dict(zip(names, row_values, strict=True)) for row_values in zip(*series_values, strict=True)
    ]


def result_columns(records: list[dict[str, Any]], names: Iterable[str]) -> dict[str, list[Any]]:
    """Turn a list of flat record dicts into a column-oriented mapping.

    Args:
        records: One record dict per row.
        names: The keys to keep, in output order. Callers drop the column
            echoing the caller's own input so the annotated frame does not
            duplicate it.
    """
    return {name: [record[name] for record in records] for name in names}


def annotate_pandas(df: Any, columns: Mapping[str, list[Any]]) -> Any:
    """Return a copy of ``df`` with ``columns`` appended."""
    annotated = df.copy()
    for name, values in columns.items():
        annotated[name] = values
    return annotated


def annotate_polars(df: Any, columns: Mapping[str, list[Any]]) -> Any:
    """Return ``df`` with ``columns`` appended."""
    import polars as pl

    return df.with_columns([pl.Series(name, values) for name, values in columns.items()])


def build_pandas(records: list[dict[str, Any]]) -> Any:
    """Build a fresh pandas DataFrame from flat record dicts.

    Raises:
        InvalidInputError: If pandas is not installed.
    """
    try:
        import pandas as pd  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - depends on env
        raise InvalidInputError(
            "to_pandas() requires pandas. Install it with `pip install helakit[pandas]`."
        ) from exc
    return pd.DataFrame(records)


def build_polars(records: list[dict[str, Any]]) -> Any:
    """Build a fresh polars DataFrame from flat record dicts.

    Raises:
        InvalidInputError: If polars is not installed.
    """
    try:
        import polars as pl
    except ImportError as exc:  # pragma: no cover - depends on env
        raise InvalidInputError(
            "to_polars() requires polars. Install it with `pip install helakit[polars]`."
        ) from exc
    return pl.DataFrame(records)


def frame_library(df: Any) -> str:
    """Return ``"pandas"``, ``"polars"``, or ``""`` for anything else."""
    if df is None:
        return ""
    root = type(df).__module__.split(".", 1)[0]
    return root if root in ("pandas", "polars") else ""
