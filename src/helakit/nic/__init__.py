"""NIC (National Identity Card) validation."""

from helakit.nic.exceptions import NICError
from helakit.nic.validator import is_valid_nic, validate_nic

__all__ = [
    "NICError",
    "is_valid_nic",
    "validate_nic",
]
