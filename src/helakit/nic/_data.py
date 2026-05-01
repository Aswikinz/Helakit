"""Constants used while decoding Sri Lankan NIC numbers.

Sri Lankan NICs encode the holder's date of birth as the day-of-year, with
female DOBs offset by 500. Old-format NICs use a two-digit year and end in
a letter (V/X) for voting eligibility; new-format NICs are fully numeric
and use a four-digit year.
"""

from __future__ import annotations

from typing import Final

OLD_FORMAT_LENGTH: Final[int] = 10
NEW_FORMAT_LENGTH: Final[int] = 12

FEMALE_DAY_OFFSET: Final[int] = 500
MIN_DAY_CODE: Final[int] = 1
MAX_DAY_CODE: Final[int] = 366

OLD_FORMAT_SUFFIXES: Final[frozenset[str]] = frozenset({"V", "X"})
DEFAULT_OLD_NIC_CENTURY: Final[int] = 1900

GENDER_MALE: Final[str] = "male"
GENDER_FEMALE: Final[str] = "female"
