"""Constants used while decoding NIC numbers.

Sri Lankan NICs encode the holder's date of birth as the day-of-year, with
female DOBs offset by 500. Old-format NICs use a two-digit year and end in
a letter (V/X) for voting eligibility; new-format NICs are fully numeric
and use a four-digit year. The exact encoding rules will live here.
"""

from __future__ import annotations

from typing import Final

OLD_FORMAT_LENGTH: Final[int] = 10
NEW_FORMAT_LENGTH: Final[int] = 12

FEMALE_DAY_OFFSET: Final[int] = 500

OLD_FORMAT_SUFFIXES: Final[frozenset[str]] = frozenset({"V", "X"})
