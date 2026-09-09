"""Districts of Sri Lanka, keyed by short code, and the province each sits in.

Sources:
    - Department of Census and Statistics, Sri Lanka:
      http://www.statistics.gov.lk/
"""

from __future__ import annotations

from typing import Final

DISTRICTS: Final[dict[str, str]] = {
    # Western Province
    "CMB": "Colombo",
    "GMP": "Gampaha",
    "KAL": "Kalutara",
    # Central Province
    "KAN": "Kandy",
    "MTL": "Matale",
    "NUE": "Nuwara Eliya",
    # Southern Province
    "GAL": "Galle",
    "MAT": "Matara",
    "HAM": "Hambantota",
    # Northern Province
    "JAF": "Jaffna",
    "KIL": "Kilinochchi",
    "MAN": "Mannar",
    "VAV": "Vavuniya",
    "MUL": "Mullaitivu",
    # Eastern Province
    "TRI": "Trincomalee",
    "BAT": "Batticaloa",
    "AMP": "Ampara",
    # North Western Province
    "KUR": "Kurunegala",
    "PUT": "Puttalam",
    # North Central Province
    "ANU": "Anuradhapura",
    "POL": "Polonnaruwa",
    # Uva Province
    "BAD": "Badulla",
    "MON": "Monaragala",
    # Sabaragamuwa Province
    "RAT": "Ratnapura",
    "KEG": "Kegalle",
}

DISTRICT_PROVINCE: Final[dict[str, str]] = {
    # Western Province
    "CMB": "WP",
    "GMP": "WP",
    "KAL": "WP",
    # Central Province
    "KAN": "CP",
    "MTL": "CP",
    "NUE": "CP",
    # Southern Province
    "GAL": "SP",
    "MAT": "SP",
    "HAM": "SP",
    # Northern Province
    "JAF": "NP",
    "KIL": "NP",
    "MAN": "NP",
    "VAV": "NP",
    "MUL": "NP",
    # Eastern Province
    "TRI": "EP",
    "BAT": "EP",
    "AMP": "EP",
    # North Western Province
    "KUR": "NW",
    "PUT": "NW",
    # North Central Province
    "ANU": "NC",
    "POL": "NC",
    # Uva Province
    "BAD": "UP",
    "MON": "UP",
    # Sabaragamuwa Province
    "RAT": "SG",
    "KEG": "SG",
}
