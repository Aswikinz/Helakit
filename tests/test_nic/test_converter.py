"""Tests for NIC format conversion."""

from __future__ import annotations

import pytest

from helakit import NICFormatError, convert_nic


def test_old_to_new() -> None:
    assert convert_nic("820149894V") == "198201409894"


def test_old_with_x_suffix() -> None:
    assert convert_nic("820149894X") == "198201409894"


def test_new_passes_through_unchanged() -> None:
    assert convert_nic("198201409894") == "198201409894"


def test_normalises_input() -> None:
    assert convert_nic("  820149894v ") == "198201409894"


def test_century_override() -> None:
    assert convert_nic("100149894V", century=2000) == "201001409894"


def test_invalid_input_raises() -> None:
    with pytest.raises(NICFormatError):
        convert_nic("garbage")


def test_old_with_bad_suffix_raises() -> None:
    with pytest.raises(NICFormatError):
        convert_nic("820149894Y")


def test_list_of_strings() -> None:
    assert convert_nic(["820149894V", "830250995X"]) == [
        "198201409894",
        "198302500995",
    ]
