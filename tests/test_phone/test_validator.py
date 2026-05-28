"""Tests for the phone number validator."""

from __future__ import annotations

import pytest

from helakit import is_valid_phone, validate_phone
from helakit._core.exceptions import InvalidInputError
from helakit.phone import PhoneDecoded, PhoneResult

# ---------------------------------------------------------------------------
# Valid numbers — local form
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "number,carrier,line_type",
    [
        ("0712345678", "Mobitel", "mobile"),
        ("0722345678", "Mobitel", "mobile"),
        ("0762345678", "Dialog", "mobile"),
        ("0772345678", "Dialog", "mobile"),
        ("0702345678", "Dialog", "mobile"),
        ("0752345678", "Airtel", "mobile"),
        ("0782345678", "Hutch", "mobile"),
        ("0112345678", "SLT / Dialog", "fixed"),
        ("0812345678", "SLT", "fixed"),
    ],
)
def test_valid_local(number, carrier, line_type):
    result = validate_phone(number)
    assert result.is_valid
    assert result.normalized == "+94" + number[1:]
    # Attribute access (pandas-feel)
    assert result.carrier == carrier
    assert result.line_type == line_type
    assert result.local == number
    # Dict-style access still works
    assert result["carrier"] == carrier
    assert result["line_type"] == line_type
    assert result["local"] == number
    # Original .data dict still populated
    assert result.data["carrier"] == carrier


# ---------------------------------------------------------------------------
# Valid numbers — international form
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "number",
    [
        "+94712345678",
        "+94762345678",
        "+94112345678",
    ],
)
def test_valid_international(number):
    result = validate_phone(number)
    assert result.is_valid
    assert result.normalized == number
    assert result.local == "0" + number[3:]


def test_valid_international_no_plus():
    result = validate_phone("94712345678")
    assert result.is_valid
    assert result.normalized == "+94712345678"


# ---------------------------------------------------------------------------
# Formatting tolerance
# ---------------------------------------------------------------------------


def test_spaces_stripped():
    assert validate_phone("071 234 5678").is_valid


def test_hyphens_stripped():
    assert validate_phone("071-234-5678").is_valid


def test_mixed_formatting():
    assert validate_phone("+94 71-234 5678").is_valid


def test_parentheses_stripped():
    assert validate_phone("(071) 234-5678").is_valid


# ---------------------------------------------------------------------------
# is_valid_phone convenience wrapper
# ---------------------------------------------------------------------------


def test_is_valid_phone_true():
    assert is_valid_phone("0712345678") is True


def test_is_valid_phone_false():
    assert is_valid_phone("0001234567") is False


# ---------------------------------------------------------------------------
# Invalid — wrong length
# ---------------------------------------------------------------------------


def test_too_short():
    result = validate_phone("071234567")  # 9 digits
    assert not result.is_valid
    assert any(e.code == "phone.invalid_length" for e in result.errors)


def test_too_long():
    result = validate_phone("07123456789")  # 11 digits local
    assert not result.is_valid
    assert any(e.code == "phone.invalid_length" for e in result.errors)


# ---------------------------------------------------------------------------
# Invalid — unknown / bad prefix
# ---------------------------------------------------------------------------


def test_unknown_prefix():
    result = validate_phone("0001234567")
    assert not result.is_valid
    assert any(e.code == "phone.unknown_prefix" for e in result.errors)


def test_missing_prefix_bare_digits():
    result = validate_phone("712345678")  # no leading 0 or country code
    assert not result.is_valid
    assert any(e.code == "phone.missing_prefix" for e in result.errors)


# ---------------------------------------------------------------------------
# Invalid — bad characters
# ---------------------------------------------------------------------------


def test_alpha_characters():
    result = validate_phone("07ABCDEFGH")
    assert not result.is_valid
    assert any(e.code == "phone.invalid_characters" for e in result.errors)


def test_empty_string():
    result = validate_phone("")
    assert not result.is_valid


def test_special_characters():
    result = validate_phone("071#234567")
    assert not result.is_valid


# ---------------------------------------------------------------------------
# Type safety
# ---------------------------------------------------------------------------


def test_non_string_raises():
    with pytest.raises(InvalidInputError):
        validate_phone(712345678)  # type: ignore[arg-type]


def test_none_raises():
    with pytest.raises(InvalidInputError):
        validate_phone(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Result structure
# ---------------------------------------------------------------------------


def test_invalid_result_has_no_normalized():
    result = validate_phone("0001234567")
    assert result.normalized is None


def test_valid_result_bool_true():
    assert bool(validate_phone("0712345678")) is True


def test_invalid_result_bool_false():
    assert bool(validate_phone("0001234567")) is False


def test_result_is_phone_result_instance():
    result = validate_phone("0712345678")
    assert isinstance(result, PhoneResult)


# ---------------------------------------------------------------------------
# Typed decoded payload
# ---------------------------------------------------------------------------


def test_decoded_payload_is_dataclass():
    result = validate_phone("0712345678")
    decoded = result.decoded
    assert isinstance(decoded, PhoneDecoded)
    assert decoded.carrier == "Mobitel"
    assert decoded.line_type == "mobile"
    assert decoded.local == "0712345678"


def test_decoded_also_accessible_via_data():
    """Backwards compatibility: ``data["decoded"]`` still works."""
    result = validate_phone("0712345678")
    assert result.data["decoded"] is result.decoded


# ---------------------------------------------------------------------------
# Pandas-like access patterns on the result
# ---------------------------------------------------------------------------


def test_attribute_access_on_invalid_returns_none():
    """Properties never raise — they return None when the field wasn't set."""
    result = validate_phone("0001234567")
    assert result.carrier is None
    assert result.line_type is None
    assert result.local is None
    assert result.decoded is None


def test_dict_access_on_invalid_raises_keyerror():
    """Dict-style access still raises, matching pandas/dict semantics."""
    result = validate_phone("0001234567")
    with pytest.raises(KeyError):
        result["carrier"]


def test_contains_check():
    result = validate_phone("0712345678")
    assert "carrier" in result
    assert "missing" not in result


def test_get_with_default():
    result = validate_phone("0001234567")
    assert result.get("carrier") is None
    assert result.get("carrier", "Unknown") == "Unknown"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_whitespace_only():
    result = validate_phone("   \t  ")
    assert not result.is_valid
    assert any(e.code == "phone.invalid_characters" for e in result.errors)


def test_internal_plus_rejected():
    result = validate_phone("07+12345678")
    assert not result.is_valid
    assert any(e.code == "phone.invalid_characters" for e in result.errors)


def test_unicode_digits_rejected():
    """Arabic-Indic digits (U+0660..U+0669) must not be treated as ASCII digits."""
    result = validate_phone("٠٧١٢٣٤٥٦٧٨")
    assert not result.is_valid
    assert any(e.code == "phone.invalid_characters" for e in result.errors)


def test_very_long_input():
    result = validate_phone("0712345678" * 10)
    assert not result.is_valid


def test_only_country_code_rejected():
    result = validate_phone("+94")
    assert not result.is_valid


def test_plus_without_digits():
    result = validate_phone("+")
    assert not result.is_valid
    assert any(e.code == "phone.invalid_characters" for e in result.errors)
