"""Tests for the scalar NIC validator."""

from __future__ import annotations

from datetime import date

import pytest

from helakit import (
    InvalidInputError,
    NICDecoded,
    is_valid_nic,
    validate_nic,
)

# ---------- Happy paths ----------


def test_old_format_valid() -> None:
    result = validate_nic("820149894V")
    assert result.is_valid
    assert result.normalized == "820149894"
    decoded = result.data["decoded"]
    assert isinstance(decoded, NICDecoded)
    assert decoded.format == "old"
    assert decoded.dob == date(1982, 1, 14)
    assert decoded.gender == "male"
    assert decoded.serial == 989
    assert decoded.check_digit == 4
    assert decoded.voting_eligible is True


def test_old_format_non_voter() -> None:
    result = validate_nic("820149894X")
    assert result.is_valid
    assert result.data["decoded"].voting_eligible is False


def test_new_format_valid() -> None:
    result = validate_nic("199201409894")
    assert result.is_valid
    assert result.normalized == "199201409894"
    decoded = result.data["decoded"]
    assert decoded.format == "new"
    assert decoded.dob == date(1992, 1, 14)
    assert decoded.gender == "male"
    assert decoded.voting_eligible is None


def test_female_offset_decoded() -> None:
    # day 514 = female, day_code 14 -> Jan 14
    result = validate_nic("199251412341")
    assert result.is_valid
    assert result.data["decoded"].gender == "female"
    assert result.data["decoded"].dob == date(1992, 1, 14)


def test_input_normalisation() -> None:
    result = validate_nic("  820149894v  ")
    assert result.is_valid
    assert result.normalized == "820149894"


# ---------- Error paths ----------


def test_bad_length() -> None:
    result = validate_nic("123")
    assert not result.is_valid
    assert [e.code for e in result.errors] == ["nic.bad_length"]


def test_old_non_numeric() -> None:
    result = validate_nic("82A14989AV")
    assert not result.is_valid
    assert any(e.code == "nic.non_numeric" for e in result.errors)


def test_new_non_numeric() -> None:
    result = validate_nic("19920140989A")
    assert not result.is_valid
    assert any(e.code == "nic.non_numeric" for e in result.errors)


def test_old_bad_suffix() -> None:
    result = validate_nic("820149894Y")
    assert not result.is_valid
    assert any(e.code == "nic.bad_suffix" for e in result.errors)


def test_old_no_suffix_letter() -> None:
    # 9 digits + a digit = 10 digits, no V/X
    result = validate_nic("8201498940")
    assert not result.is_valid
    assert any(e.code == "nic.bad_suffix" for e in result.errors)


def test_day_code_out_of_range() -> None:
    # raw day code 400 is invalid (>366, <500 so still male)
    result = validate_nic("199240001231")
    assert not result.is_valid
    assert any(e.code == "nic.bad_day_code" for e in result.errors)


def test_female_day_code_out_of_range() -> None:
    # raw 900 = female + 400 -> day_code 400, invalid
    result = validate_nic("199290001231")
    assert not result.is_valid
    assert any(e.code == "nic.bad_day_code" for e in result.errors)


def test_phantom_feb_29_in_non_leap_year() -> None:
    # 1999 is non-leap; day 60 is the phantom Feb 29
    result = validate_nic("199906012345")
    assert not result.is_valid
    assert any(e.code == "nic.invalid_date" for e in result.errors)


def test_day_366_in_non_leap_year_decodes_to_dec_31() -> None:
    # NIC always reserves 366 codes; in non-leap years the phantom Feb 29
    # at code 60 is wasted, so day 366 still maps to Dec 31.
    result = validate_nic("199936612345")
    assert result.is_valid
    assert result.data["decoded"].dob == date(1999, 12, 31)


def test_day_366_in_leap_year_valid() -> None:
    result = validate_nic("200036612345")
    assert result.is_valid
    assert result.data["decoded"].dob == date(2000, 12, 31)


def test_year_zero_new_format_is_invalid_not_a_crash() -> None:
    # A "0000…" new-format NIC decodes to year 0, which is outside the range
    # datetime.date can represent. It must surface as a validation error, not
    # raise (malformed data is always reported through the result).
    result = validate_nic("000020000018")
    assert not result.is_valid
    assert any(e.code == "nic.invalid_date" for e in result.errors)


# ---------- Format hint ----------


def test_format_hint_old_rejects_new() -> None:
    result = validate_nic("199201409894", format="old")
    assert not result.is_valid
    assert any(e.code == "nic.format_mismatch" for e in result.errors)


def test_format_hint_new_rejects_old() -> None:
    result = validate_nic("820149894V", format="new")
    assert not result.is_valid
    assert any(e.code == "nic.format_mismatch" for e in result.errors)


# ---------- Leap-year encoding ----------


def test_feb_29_in_leap_year() -> None:
    result = validate_nic("200006012345")  # 2000 is leap
    assert result.is_valid
    assert result.data["decoded"].dob == date(2000, 2, 29)


def test_march_1_in_non_leap_year_uses_day_61() -> None:
    # In non-leap year, Mar 1 encodes as day 61, not 60
    result = validate_nic("198206112345")
    assert result.is_valid
    assert result.data["decoded"].dob == date(1982, 3, 1)


def test_march_1_in_leap_year_uses_day_61() -> None:
    result = validate_nic("200006112345")
    assert result.is_valid
    assert result.data["decoded"].dob == date(2000, 3, 1)


def test_old_nic_century_override() -> None:
    # Force 2000s for an old NIC with two-digit year "10"
    result = validate_nic("100149894V", century=2000)
    assert result.is_valid
    assert result.data["decoded"].year == 2010


# ---------- Boolean shorthand ----------


def test_is_valid_nic_true() -> None:
    assert is_valid_nic("820149894V") is True
    assert is_valid_nic("199201409894") is True


def test_is_valid_nic_false() -> None:
    assert is_valid_nic("garbage") is False


def test_is_valid_nic_format_filter() -> None:
    assert is_valid_nic("820149894V", format="old") is True
    assert is_valid_nic("820149894V", format="new") is False


def test_is_valid_nic_rejects_non_string() -> None:
    with pytest.raises(InvalidInputError):
        is_valid_nic(12345)  # type: ignore[arg-type]


# ---------- Truthiness / repr ----------


def test_validation_result_is_truthy_when_valid() -> None:
    assert bool(validate_nic("820149894V")) is True
    assert bool(validate_nic("xxx")) is False
