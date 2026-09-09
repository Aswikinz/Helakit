"""Value coercion for the NIC validator's cross-check columns.

Input-type detection itself lives in :mod:`helakit._core.dispatch` and is shared
with the other batch-capable validators; ``detect_kind`` and ``InputKind`` are
re-exported here so NIC call-sites keep importing from one place.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from helakit._core.dispatch import InputKind, detect_kind, is_na
from helakit._core.exceptions import InvalidInputError

__all__ = ["InputKind", "coerce_dob", "coerce_gender", "detect_kind"]

_VALID_GENDER_TOKENS: dict[str, Literal["male", "female"]] = {
    "m": "male",
    "male": "male",
    "f": "female",
    "female": "female",
}


def coerce_gender(value: Any) -> Literal["male", "female"] | None:
    """Normalise an arbitrary gender input to ``"male"`` / ``"female"``.

    Accepts ``"M"``, ``"F"``, ``"male"``, ``"female"`` in any letter case.
    Treats ``None`` and pandas/numpy NA sentinels as "no value supplied".

    Raises:
        InvalidInputError: For anything else (e.g. ``"other"``, ``1``).
    """
    if is_na(value):
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
    if is_na(value):
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
