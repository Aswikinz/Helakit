"""Placeholder tests for the phone validator stubs."""

from __future__ import annotations

import pytest
from helakit import is_valid_phone, validate_phone


def test_validate_phone_is_stubbed() -> None:
    with pytest.raises(NotImplementedError):
        validate_phone("0712345678")


def test_is_valid_phone_is_stubbed() -> None:
    with pytest.raises(NotImplementedError):
        is_valid_phone("0712345678")
