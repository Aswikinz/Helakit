"""Parse a NIC string into structured fields.

This module is the single source of truth for breaking a NIC apart. Both
``validate_nic`` and ``convert_nic`` funnel through :func:`parse` so the
encoding rules live in exactly one place.

Notes on day-of-year encoding:
    Sri Lankan NICs reserve day 60 for February 29 in *every* year, leap
    or not. In a non-leap year day 60 is therefore a phantom date with no
    real calendar equivalent and is treated as invalid. Days 61-366 in a
    non-leap year shift down by one when mapped onto the actual 365-day
    calendar.

Notes on the check digit:
    The Department for Registration of Persons has not published the
    modulo-11 algorithm used to compute NIC check digits, and no public
    implementation has reverse-engineered it. We extract the digit but do
    not verify it; if the algorithm ever becomes available, validation
    can be added without changing the public API.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from helakit._core.result import ValidationError
from helakit.nic._data import (
    DEFAULT_OLD_NIC_CENTURY,
    FEMALE_DAY_OFFSET,
    GENDER_FEMALE,
    GENDER_MALE,
    MAX_DAY_CODE,
    MIN_DAY_CODE,
    NEW_FORMAT_LENGTH,
    OLD_FORMAT_LENGTH,
    OLD_FORMAT_SUFFIXES,
)
from helakit.nic._normalize import normalize


@dataclass(frozen=True, slots=True)
class ParsedNIC:
    """The structured view of a NIC after parsing.

    ``dob`` is ``None`` if the day-of-year code does not yield a valid
    calendar date in the given year (for example day 60 in a non-leap
    year, or day 366 in a non-leap year).
    """

    format: Literal["old", "new"]
    year: int
    day_code: int
    raw_day_code: int
    serial: int
    check_digit: int
    voting_eligible: bool | None
    dob: date | None
    gender: Literal["male", "female"]


def parse(
    value: str, *, century: int = DEFAULT_OLD_NIC_CENTURY
) -> tuple[ParsedNIC | None, list[ValidationError]]:
    """Parse ``value`` as either an old- or new-format NIC.

    Returns ``(parsed, errors)``. ``parsed`` is ``None`` when the input is
    so malformed that no fields can be extracted; otherwise it is always
    populated, even if some checks failed (in which case those failures
    appear in ``errors``).
    """
    cleaned = normalize(value)
    length = len(cleaned)

    if length == OLD_FORMAT_LENGTH:
        return _parse_old(cleaned, century=century)
    if length == NEW_FORMAT_LENGTH:
        return _parse_new(cleaned)

    return None, [
        ValidationError(
            code="nic.bad_length",
            message=(
                f"NIC must be {OLD_FORMAT_LENGTH} (old) or {NEW_FORMAT_LENGTH} (new) "
                f"characters; got {length}."
            ),
        )
    ]


def _parse_old(value: str, *, century: int) -> tuple[ParsedNIC | None, list[ValidationError]]:
    errors: list[ValidationError] = []
    digits, suffix = value[:-1], value[-1]

    if not digits.isdigit():
        return None, [
            ValidationError(
                code="nic.non_numeric",
                message="Old NIC must contain 9 digits before the trailing letter.",
            )
        ]

    if suffix not in OLD_FORMAT_SUFFIXES:
        errors.append(
            ValidationError(
                code="nic.bad_suffix",
                message=(f"Old NIC must end with 'V' or 'X'; got {suffix!r}."),
                field="suffix",
            )
        )

    year = century + int(digits[:2])
    raw_day_code = int(digits[2:5])
    serial = int(digits[5:8])
    check_digit = int(digits[8])

    return _build_parsed(
        fmt="old",
        year=year,
        raw_day_code=raw_day_code,
        serial=serial,
        check_digit=check_digit,
        suffix=suffix,
        errors=errors,
    )


def _parse_new(value: str) -> tuple[ParsedNIC | None, list[ValidationError]]:
    if not value.isdigit():
        return None, [
            ValidationError(
                code="nic.non_numeric",
                message="New NIC must contain only digits.",
            )
        ]

    year = int(value[:4])
    raw_day_code = int(value[4:7])
    serial = int(value[7:11])
    check_digit = int(value[11])

    return _build_parsed(
        fmt="new",
        year=year,
        raw_day_code=raw_day_code,
        serial=serial,
        check_digit=check_digit,
        suffix=None,
        errors=[],
    )


def _build_parsed(
    *,
    fmt: Literal["old", "new"],
    year: int,
    raw_day_code: int,
    serial: int,
    check_digit: int,
    suffix: str | None,
    errors: list[ValidationError],
) -> tuple[ParsedNIC | None, list[ValidationError]]:
    if raw_day_code >= FEMALE_DAY_OFFSET:
        gender: Literal["male", "female"] = GENDER_FEMALE  # type: ignore[assignment]
        day_code = raw_day_code - FEMALE_DAY_OFFSET
    else:
        gender = GENDER_MALE  # type: ignore[assignment]
        day_code = raw_day_code

    dob: date | None = None
    if day_code < MIN_DAY_CODE or day_code > MAX_DAY_CODE:
        errors.append(
            ValidationError(
                code="nic.bad_day_code",
                message=(
                    f"Day-of-year encoding {raw_day_code} is out of range. "
                    "Expected 1-366 (male) or 501-866 (female)."
                ),
                field="day_code",
            )
        )
    else:
        dob = _day_to_date(year, day_code)
        if dob is None:
            errors.append(
                ValidationError(
                    code="nic.invalid_date",
                    message=(
                        f"Day code {raw_day_code} does not correspond to a real date in {year}."
                    ),
                    field="day_code",
                )
            )

    parsed = ParsedNIC(
        format=fmt,
        year=year,
        day_code=day_code,
        raw_day_code=raw_day_code,
        serial=serial,
        check_digit=check_digit,
        voting_eligible=(suffix == "V") if fmt == "old" else None,
        dob=dob,
        gender=gender,
    )
    return parsed, errors


def _day_to_date(year: int, day_code: int) -> date | None:
    """Map an SL-NIC day-of-year code to a calendar date.

    Returns ``None`` if the code does not correspond to a real date in the
    given year (phantom Feb 29, or day 366 outside a leap year).
    """
    if day_code < MIN_DAY_CODE or day_code > MAX_DAY_CODE:
        return None
    if calendar.isleap(year):
        return date(year, 1, 1) + timedelta(days=day_code - 1)
    if day_code == 60:
        return None
    if day_code > 60:
        day_code -= 1
    if day_code > 365:
        return None
    return date(year, 1, 1) + timedelta(days=day_code - 1)


def date_to_day_code(value: date) -> int:
    """Encode a calendar date as an SL-NIC day-of-year code.

    Days from March onwards in a non-leap year shift up by one to leave
    room for the always-reserved Feb 29 slot at code 60.
    """
    yday = value.timetuple().tm_yday
    if not calendar.isleap(value.year) and value.month >= 3:
        yday += 1
    return yday
