"""Typed result payloads for the phone validator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

LineType = Literal["mobile", "fixed"]


@dataclass(frozen=True, slots=True)
class PhoneDecoded:
    """Structured metadata returned in ``ValidationResult.data["decoded"]``."""

    carrier: str
    line_type: LineType
    local: str
