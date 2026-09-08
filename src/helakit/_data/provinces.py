"""Provinces of Sri Lanka, keyed by short code.

Sources:
    - Department of Census and Statistics, Sri Lanka:
      http://www.statistics.gov.lk/
"""

from __future__ import annotations

from typing import Final

PROVINCES: Final[dict[str, str]] = {
    "WP": "Western",
    "CP": "Central",
    "SP": "Southern",
    "NP": "Northern",
    "EP": "Eastern",
    "NW": "North Western",
    "NC": "North Central",
    "UP": "Uva",
    "SG": "Sabaragamuwa",
}
