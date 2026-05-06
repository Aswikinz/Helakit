"""Sri Lankan phone-number prefix data.

Prefixes are three digits (the leading ``0`` plus two more). Each entry maps
to a carrier name and a line type (``"mobile"`` or ``"fixed"``).

Sources:
    - Telecommunications Regulatory Commission of Sri Lanka (TRCSL):
      https://www.trc.gov.lk/
    - Dialog, Mobitel, Hutch, Airtel, SLT published prefix lists.
"""

from __future__ import annotations

from typing import Final, NamedTuple

from helakit.phone._types import LineType


class PrefixInfo(NamedTuple):
    carrier: str
    line_type: LineType


# ---------------------------------------------------------------------------
# Mobile prefixes
# ---------------------------------------------------------------------------
MOBILE_PREFIXES: Final[dict[str, PrefixInfo]] = {
    # Dialog
    "070": PrefixInfo("Dialog", "mobile"),
    "076": PrefixInfo("Dialog", "mobile"),
    "077": PrefixInfo("Dialog", "mobile"),
    # Mobitel (Sri Lanka Telecom)
    "071": PrefixInfo("Mobitel", "mobile"),
    "072": PrefixInfo("Mobitel", "mobile"),
    # Hutch (now Hutch / previously Tigo/Celltel)
    "078": PrefixInfo("Hutch", "mobile"),
    # Airtel
    "075": PrefixInfo("Airtel", "mobile"),
    # Lanka Bell (CDMA mobile)
    "079": PrefixInfo("Lanka Bell", "mobile"),
    # Dhiraagu (roaming / special)
    "074": PrefixInfo("Dialog", "mobile"),
}

# ---------------------------------------------------------------------------
# Fixed-line area-code prefixes (two-digit area codes, stored as "0XX")
# ---------------------------------------------------------------------------
FIXED_PREFIXES: Final[dict[str, PrefixInfo]] = {
    "011": PrefixInfo("SLT / Dialog", "fixed"),  # Colombo
    "031": PrefixInfo("SLT", "fixed"),  # Negombo
    "032": PrefixInfo("SLT", "fixed"),  # Kurunegala
    "033": PrefixInfo("SLT", "fixed"),  # Gampaha
    "034": PrefixInfo("SLT", "fixed"),  # Kalutara
    "035": PrefixInfo("SLT", "fixed"),  # Kegalle
    "036": PrefixInfo("SLT", "fixed"),  # Avissawella
    "037": PrefixInfo("SLT", "fixed"),  # Kurunegala (alt)
    "038": PrefixInfo("SLT", "fixed"),  # Panadura
    "041": PrefixInfo("SLT", "fixed"),  # Galle
    "045": PrefixInfo("SLT", "fixed"),  # Ratnapura
    "047": PrefixInfo("SLT", "fixed"),  # Hambantota
    "051": PrefixInfo("SLT", "fixed"),  # Nuwara Eliya / Kandy
    "052": PrefixInfo("SLT", "fixed"),  # Nuwara Eliya
    "054": PrefixInfo("SLT", "fixed"),  # Matale
    "055": PrefixInfo("SLT", "fixed"),  # Badulla
    "057": PrefixInfo("SLT", "fixed"),  # Bandarawela
    "063": PrefixInfo("SLT", "fixed"),  # Ampara
    "065": PrefixInfo("SLT", "fixed"),  # Batticaloa
    "066": PrefixInfo("SLT", "fixed"),  # Polonnaruwa
    "067": PrefixInfo("SLT", "fixed"),  # Kalmunai
    "081": PrefixInfo("SLT", "fixed"),  # Kandy
    "091": PrefixInfo("SLT", "fixed"),  # Galle (alt)
}

# Combined lookup
ALL_PREFIXES: Final[dict[str, PrefixInfo]] = {**MOBILE_PREFIXES, **FIXED_PREFIXES}

# ---------------------------------------------------------------------------
# Length rules
# ---------------------------------------------------------------------------
LOCAL_LENGTH: Final[int] = 10  # 0XX-XXXXXXX  (10 digits)
INTL_PREFIX: Final[str] = "+94"
INTL_LENGTH: Final[int] = 11  # 94XXXXXXXXX  (11 digits, no leading 0)
COUNTRY_CODE: Final[str] = "94"
