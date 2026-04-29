"""Placeholder tests for the NIC validator stubs."""

from __future__ import annotations

import pytest
from helakit import is_valid_nic, validate_nic


def test_validate_nic_is_stubbed() -> None:
    with pytest.raises(NotImplementedError):
        validate_nic("199012345678")


def test_is_valid_nic_is_stubbed() -> None:
    with pytest.raises(NotImplementedError):
        is_valid_nic("199012345678")
