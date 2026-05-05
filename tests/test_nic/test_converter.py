"""Tests for NIC format conversion."""

from __future__ import annotations

import pytest

from helakit import InvalidInputError, NICFormatError, convert_nic


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


def test_list_default_raises_on_first_bad_value() -> None:
    with pytest.raises(NICFormatError):
        convert_nic(["820149894V", "garbage"])


def test_list_errors_coerce_replaces_bad_values_with_none() -> None:
    assert convert_nic(["820149894V", "garbage", "830250995X"], errors="coerce") == [
        "198201409894",
        None,
        "198302500995",
    ]


def test_list_errors_ignore_keeps_originals() -> None:
    assert convert_nic(["820149894V", "garbage"], errors="ignore") == [
        "198201409894",
        "garbage",
    ]


def test_list_errors_invalid_value_raises() -> None:
    with pytest.raises(InvalidInputError):
        convert_nic(["820149894V"], errors="silently-fail")  # type: ignore[arg-type]


def test_list_error_col_rejected() -> None:
    with pytest.raises(InvalidInputError):
        convert_nic(["820149894V"], error_col="err")


def test_scalar_error_col_rejected() -> None:
    with pytest.raises(InvalidInputError):
        convert_nic("820149894V", error_col="err")


def test_list_coerce_handles_non_string_input() -> None:
    assert convert_nic(["820149894V", None, 42], errors="coerce") == [  # type: ignore[list-item]
        "198201409894",
        None,
        None,
    ]
