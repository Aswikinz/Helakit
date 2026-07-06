"""Tests for the pandas-feel access patterns on NicResult."""

from __future__ import annotations

from datetime import date

import pytest

from helakit import NICDecoded, NicResult, validate_nic


def test_returns_nic_result_instance() -> None:
    result = validate_nic("199201409894")
    assert isinstance(result, NicResult)


def test_typed_attribute_access() -> None:
    """Typed properties match the existing data["decoded"] payload."""
    result = validate_nic("199201409894")
    assert result.is_valid
    decoded = result.data["decoded"]
    assert isinstance(decoded, NICDecoded)

    assert result.decoded is decoded
    assert result.format == decoded.format
    assert result.dob == decoded.dob
    assert result.gender == decoded.gender
    assert result.age == decoded.age
    assert result.year == decoded.year
    assert result.serial == decoded.serial
    assert result.voting_eligible == decoded.voting_eligible


def test_age_at_is_deterministic_for_a_fixed_reference_date() -> None:
    """age_at takes an explicit date, so it never depends on the wall clock."""
    result = validate_nic("199201409894")  # DOB 1992-01-14
    decoded = result.decoded
    assert decoded is not None
    assert decoded.age_at(date(2026, 1, 14)) == 34  # birthday reached
    assert decoded.age_at(date(2026, 1, 13)) == 33  # day before birthday
    assert result.age_at(date(2026, 1, 14)) == 34  # same via the result


def test_age_is_not_a_stored_constructor_field() -> None:
    """Age depends on the current date, so it must not be baked into the
    immutable decoded payload."""
    with pytest.raises(TypeError):
        NICDecoded(  # type: ignore[call-arg]
            format="new",
            dob=date(1992, 1, 14),
            gender="male",
            age=33,
            year=1992,
            day_code=14,
            serial=989,
            check_digit=4,
            voting_eligible=None,
        )


def test_dict_style_access() -> None:
    """`result["decoded"]` mirrors `result.data["decoded"]`."""
    result = validate_nic("199201409894")
    assert result["decoded"] is result.data["decoded"]
    assert result["format"] == "new"


def test_attribute_access_on_invalid_returns_none() -> None:
    """All typed properties should return None on invalid input — never raise."""
    result = validate_nic("garbage")
    assert not result.is_valid
    assert result.decoded is None
    assert result.dob is None
    assert result.gender is None
    assert result.age is None
    assert result.year is None
    assert result.serial is None
    assert result.voting_eligible is None
    assert result.format is None


def test_dict_access_on_invalid_raises_keyerror() -> None:
    result = validate_nic("garbage")
    with pytest.raises(KeyError):
        result["decoded"]


def test_contains_and_get() -> None:
    valid = validate_nic("199201409894")
    invalid = validate_nic("garbage")

    assert "decoded" in valid
    assert "decoded" not in invalid

    assert valid.get("decoded") is valid.decoded
    assert invalid.get("decoded") is None
    assert invalid.get("decoded", "fallback") == "fallback"


def test_voting_eligible_new_format_is_none() -> None:
    """New-format NICs don't encode V/X — voting_eligible should be None."""
    result = validate_nic("199201409894")
    assert result.is_valid
    assert result.format == "new"
    assert result.voting_eligible is None


def test_old_format_voting_eligible_set() -> None:
    result = validate_nic("820149894V")
    assert result.is_valid
    assert result.format == "old"
    assert result.voting_eligible is True


def test_cross_check_properties_none_without_batch() -> None:
    """Without batch cross-check, dob_match / gender_match are None."""
    result = validate_nic("199201409894")
    assert result.dob_match is None
    assert result.gender_match is None
    assert result.mismatch_reasons is None
    assert result.mismatch_detail is None


def test_batch_results_carry_typed_access() -> None:
    """Each NicResult in a batch supports the same typed access."""
    batch = validate_nic(
        [
            {"nic": "820149894V", "dob": date(1990, 1, 1), "gender": "M"},
        ],
        nic_col="nic",
        dob_col="dob",
        gender_col="gender",
    )
    result = batch[0]
    assert isinstance(result, NicResult)
    assert result.dob_match is False
    assert result.mismatch_reasons == ["dob"]
