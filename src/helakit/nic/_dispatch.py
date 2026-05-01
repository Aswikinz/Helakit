"""Input-type detection and value coercion for the NIC validator.

The functions here let :func:`validate_nic` accept strings, lists, lists
of dicts, pandas DataFrames or polars DataFrames without importing
pandas or polars unless the caller actually passes one of those objects.
"""

from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any, Literal

from helakit._core.exceptions import InvalidInputError

InputKind = Literal["str", "list_of_str", "list_of_dict", "pandas", "polars"]

_VALID_GENDER_TOKENS: dict[str, Literal["male", "female"]] = {
    "m": "male",
    "male": "male",
    "f": "female",
    "female": "female",
}


def detect_kind(value: Any) -> InputKind:
    """Classify an input passed to :func:`validate_nic`.

    Raises:
        InvalidInputError: If the input does not match any supported kind.
    """
    if isinstance(value, str):
        return "str"

    cls = type(value)
    module = cls.__module__
    root = module.split(".", 1)[0]
    if root == "pandas":
        return "pandas"
    if root == "polars":
        return "polars"

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


def coerce_gender(value: Any) -> Literal["male", "female"] | None:
    """Normalise an arbitrary gender input to ``"male"`` / ``"female"``.

    Accepts ``"M"``, ``"F"``, ``"male"``, ``"female"`` in any letter case.
    Treats ``None`` and pandas/numpy NA sentinels as "no value supplied".

    Raises:
        InvalidInputError: For anything else (e.g. ``"other"``, ``1``).
    """
    if _is_na(value):
        return None
    if not isinstance(value, str):
        raise InvalidInputError(
            f"Gender must be a string (M/F/Male/Female); got {type(value).__name__}."
        )
    token = value.strip().lower()
    coerced = _VALID_GENDER_TOKENS.get(token)
    if coerced is None:
        raise InvalidInputError(
            f"Unrecognised gender value {value!r}. Expected one of M, F, Male, Female."
        )
    return coerced


def coerce_dob(value: Any) -> date | None:
    """Normalise an arbitrary date-of-birth input to a :class:`date`.

    Accepts ``date``, ``datetime``, ISO-format strings, and any object with
    a ``to_pydatetime()`` method (covers pandas Timestamp, numpy
    datetime64). Treats ``None`` / NA as "no value supplied".

    Raises:
        InvalidInputError: For unrecognisable inputs.
    """
    if _is_na(value):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError as exc:
            raise InvalidInputError(
                f"Could not parse {value!r} as an ISO date (YYYY-MM-DD)."
            ) from exc
    to_pydatetime = getattr(value, "to_pydatetime", None)
    if callable(to_pydatetime):
        return to_pydatetime().date()  # type: ignore[no-any-return]
    raise InvalidInputError(f"Cannot interpret {value!r} (type {type(value).__name__}) as a date.")


def _is_na(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return type(value).__name__ in {"NaTType", "Null"}
