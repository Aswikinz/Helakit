"""NIC (National Identity Card) validation, decoding, and conversion."""

from helakit.nic._types import NICBatchResult, NICDecoded, NICSummary
from helakit.nic.converter import convert_nic
from helakit.nic.exceptions import NICError, NICFormatError
from helakit.nic.validator import is_valid_nic, validate_nic

__all__ = [
    "NICBatchResult",
    "NICDecoded",
    "NICError",
    "NICFormatError",
    "NICSummary",
    "convert_nic",
    "is_valid_nic",
    "validate_nic",
]
