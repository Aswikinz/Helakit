"""Smoke tests for the static lookup tables."""

from __future__ import annotations

from helakit._data.districts import DISTRICTS
from helakit._data.provinces import PROVINCES
from helakit.nic._data import (
    FEMALE_DAY_OFFSET,
    NEW_FORMAT_LENGTH,
    OLD_FORMAT_LENGTH,
    OLD_FORMAT_SUFFIXES,
)


def test_provinces_table_has_entries() -> None:
    assert PROVINCES
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in PROVINCES.items())


def test_districts_table_has_entries() -> None:
    assert DISTRICTS
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in DISTRICTS.items())


def test_nic_format_constants() -> None:
    assert OLD_FORMAT_LENGTH == 10
    assert NEW_FORMAT_LENGTH == 12
    assert FEMALE_DAY_OFFSET == 500
    assert OLD_FORMAT_SUFFIXES == frozenset({"V", "X"})
