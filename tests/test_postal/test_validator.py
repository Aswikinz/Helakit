"""Tests for single-value postal-code validation."""

from __future__ import annotations

import pytest

from helakit import InvalidInputError, PostalDecoded, PostalResult, is_valid_postal, validate_postal

# ---- Valid codes ----------------------------------------------------------


def test_validates_a_main_post_office() -> None:
    result = validate_postal("10250")
    assert result.is_valid
    assert result.normalized == "10250"
    assert result.post_office == "Nugegoda"
    assert result.district == "Colombo"
    assert result.province == "Western"
    assert result.district_code == "CMB"
    assert result.province_code == "WP"
    assert result.sub_post is False
    assert result.errors == []


def test_validates_a_sub_post_office() -> None:
    result = validate_postal("41160")
    assert result.is_valid
    assert result.post_office == "Adampan"
    assert result.district == "Mannar"
    assert result.province == "Northern"
    assert result.sub_post is True


@pytest.mark.parametrize(
    ("code", "district", "province"),
    [
        ("00700", "Colombo", "Western"),
        ("20000", "Kandy", "Central"),
        ("40000", "Jaffna", "Northern"),
        ("30000", "Batticaloa", "Eastern"),
        ("60000", "Kurunegala", "North Western"),
        ("50000", "Anuradhapura", "North Central"),
        ("90000", "Badulla", "Uva"),
        ("70000", "Ratnapura", "Sabaragamuwa"),
        ("81000", "Matara", "Southern"),
    ],
)
def test_district_and_province_across_the_country(code, district, province) -> None:
    result = validate_postal(code)
    assert result.district == district
    assert result.province == province


def test_leading_zero_codes_are_kept() -> None:
    assert validate_postal("00100").post_office == "Colombo 01"
    assert validate_postal("00800").post_office == "Borella"


def test_result_is_truthy_when_valid() -> None:
    assert validate_postal("10250")
    assert not validate_postal("99999")


# ---- Formatting tolerance -------------------------------------------------


@pytest.mark.parametrize("raw", ["10250", " 10250 ", "102 50", "102-50", "10 2 5 0"])
def test_separators_and_whitespace_are_stripped(raw) -> None:
    result = validate_postal(raw)
    assert result.is_valid
    assert result.normalized == "10250"
    assert result.value == raw


# ---- Error codes ----------------------------------------------------------


@pytest.mark.parametrize("raw", ["", "   ", "abcde", "1025O", "102.5", "١٠٢٥٠"])
def test_invalid_characters(raw) -> None:
    result = validate_postal(raw)
    assert not result.is_valid
    assert [e.code for e in result.errors] == ["postal.invalid_characters"]


@pytest.mark.parametrize("raw", ["1", "102", "1025", "102500", "0000000"])
def test_invalid_length(raw) -> None:
    result = validate_postal(raw)
    assert not result.is_valid
    assert [e.code for e in result.errors] == ["postal.invalid_length"]


def test_invalid_length_message_mentions_leading_zeros() -> None:
    assert "leading zeros" in validate_postal("700").errors[0].message


@pytest.mark.parametrize("raw", ["99999", "00000", "12345"])
def test_unknown_code(raw) -> None:
    result = validate_postal(raw)
    assert not result.is_valid
    assert [e.code for e in result.errors] == ["postal.unknown_code"]


def test_invalid_result_exposes_no_fields() -> None:
    result = validate_postal("99999")
    assert result.normalized is None
    assert result.post_office is None
    assert result.district is None
    assert result.province is None
    assert result.sub_post is None
    assert result.decoded is None


# ---- Misuse ---------------------------------------------------------------


@pytest.mark.parametrize("bad", [None, 10250, 10250.0, True, b"10250"])
def test_non_string_scalar_is_a_programmer_error(bad) -> None:
    with pytest.raises(InvalidInputError):
        validate_postal(bad)


def test_invalid_errors_mode_is_rejected() -> None:
    with pytest.raises(InvalidInputError, match="errors must be one of"):
        validate_postal(["10250"], errors="nonsense")  # type: ignore[arg-type]


# ---- is_valid_postal ------------------------------------------------------


def test_is_valid_postal_shorthand() -> None:
    assert is_valid_postal("10250") is True
    assert is_valid_postal("99999") is False
    assert is_valid_postal(" 102 50 ") is True


def test_is_valid_postal_rejects_non_strings() -> None:
    with pytest.raises(InvalidInputError):
        is_valid_postal(10250)  # type: ignore[arg-type]


# ---- Typed / dict-style access -------------------------------------------


def test_decoded_payload() -> None:
    decoded = validate_postal("10250").decoded
    assert isinstance(decoded, PostalDecoded)
    assert decoded.post_office == "Nugegoda"
    assert decoded.district_code == "CMB"
    assert decoded.province_code == "WP"
    assert decoded.sub_post is False


def test_dict_style_access() -> None:
    result = validate_postal("10250")
    assert result["district"] == "Colombo"
    assert "province" in result
    assert result.get("missing", "n/a") == "n/a"
    assert set(result) >= {"post_office", "district", "province"}
    with pytest.raises(KeyError):
        result["nope"]


def test_to_dict_matches_record_fields() -> None:
    record = validate_postal("10250").to_dict()
    assert tuple(record) == PostalResult.record_fields()
    assert record["postal"] == "10250"
    assert record["postal_valid"] is True
    assert record["postal_post_office"] == "Nugegoda"
    assert record["postal_errors"] is None


def test_to_dict_joins_error_codes() -> None:
    assert validate_postal("99999").to_dict()["postal_errors"] == "postal.unknown_code"


def test_repr_is_readable() -> None:
    assert "is_valid=True" in repr(validate_postal("10250"))
    assert "postal.unknown_code" in repr(validate_postal("99999"))
