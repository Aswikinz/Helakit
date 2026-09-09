"""Input-type detection shared by every batch-capable validator.

Validators that accept more than a single string — :func:`~helakit.nic.validate_nic`,
:func:`~helakit.postal.validate_postal` — classify their input here first. The
detection is duck-typed on the module a class comes from, so neither pandas nor
polars is imported unless the caller actually passes one of their objects.
"""

from __future__ import annotations

import math
from typing import Any, Literal

from helakit._core.exceptions import InvalidInputError

InputKind = Literal[
    "str",
    "list_of_str",
    "list_of_dict",
    "pandas",
    "pandas_series",
    "polars",
    "polars_series",
]


def detect_kind(value: Any) -> InputKind:
    """Classify an input passed to a batch-capable validator.

    Args:
        value: Anything a validator was handed.

    Returns:
        The :data:`InputKind` describing ``value``.

    Raises:
        InvalidInputError: If the input does not match any supported kind.
    """
    if isinstance(value, str):
        return "str"

    cls = type(value)
    module = cls.__module__
    root = module.split(".", 1)[0]
    if root == "pandas":
        return "pandas_series" if cls.__name__ == "Series" else "pandas"
    if root == "polars":
        return "polars_series" if cls.__name__ == "Series" else "polars"

    if isinstance(value, (list, tuple)):
        if not value:
            return "list_of_str"
        first = value[0]
        if isinstance(first, str):
            return "list_of_str"
        if isinstance(first, dict):
            return "list_of_dict"
        raise InvalidInputError(
            f"List elements must all be strings or all be dicts; got {type(first).__name__}."
        )

    raise InvalidInputError(
        f"Unsupported input type {cls.__module__}.{cls.__qualname__}. "
        "Pass a str, list[str], list[dict], pandas.DataFrame or polars.DataFrame."
    )


def is_na(value: Any) -> bool:
    """Return ``True`` for values that mean "nothing supplied".

    Covers ``None``, float ``NaN``, and the pandas/polars null sentinels
    (``NaT``, ``Null``) without importing either library.
    """
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return type(value).__name__ in {"NaTType", "Null"}
