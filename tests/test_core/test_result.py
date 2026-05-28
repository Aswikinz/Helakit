"""Tests for :class:`ValidationResult` and :class:`ValidationError`."""

from __future__ import annotations

import pytest

from helakit import ValidationError, ValidationResult


def test_valid_result_is_truthy() -> None:
    result = ValidationResult(is_valid=True, value="x", normalized="X")
    assert result
    assert bool(result) is True


def test_invalid_result_is_falsy() -> None:
    result = ValidationResult(
        is_valid=False,
        value="x",
        errors=[ValidationError(code="bad", message="nope")],
    )
    assert not result
    assert bool(result) is False


def test_default_collections_are_independent() -> None:
    a = ValidationResult(is_valid=True, value="a")
    b = ValidationResult(is_valid=True, value="b")
    assert a.errors is not b.errors
    assert a.data is not b.data


def test_repr_distinguishes_valid_from_invalid() -> None:
    valid = ValidationResult(is_valid=True, value="x", normalized="X", data={"k": 1})
    invalid = ValidationResult(
        is_valid=False,
        value="x",
        errors=[ValidationError(code="bad", message="nope")],
    )
    assert "is_valid=True" in repr(valid)
    assert "'k': 1" in repr(valid)
    assert "is_valid=False" in repr(invalid)
    assert "'bad'" in repr(invalid)


def test_result_is_frozen() -> None:
    result = ValidationResult(is_valid=True, value="x")
    with pytest.raises(AttributeError):
        result.is_valid = False  # type: ignore[misc]


def test_error_is_frozen() -> None:
    error = ValidationError(code="bad", message="nope")
    with pytest.raises(AttributeError):
        error.code = "other"  # type: ignore[misc]


def test_error_field_defaults_to_none() -> None:
    error = ValidationError(code="bad", message="nope")
    assert error.field is None


# ---------------------------------------------------------------------------
# Dict-style access (pandas-like)
# ---------------------------------------------------------------------------


def test_getitem_reads_data_field() -> None:
    result = ValidationResult(is_valid=True, value="x", data={"carrier": "Dialog"})
    assert result["carrier"] == "Dialog"


def test_getitem_raises_keyerror_for_missing_field() -> None:
    result = ValidationResult(is_valid=True, value="x", data={"carrier": "Dialog"})
    with pytest.raises(KeyError):
        result["missing"]


def test_contains_returns_true_for_present_field() -> None:
    result = ValidationResult(is_valid=True, value="x", data={"carrier": "Dialog"})
    assert "carrier" in result
    assert "missing" not in result


def test_iter_yields_data_keys() -> None:
    result = ValidationResult(
        is_valid=True, value="x", data={"carrier": "Dialog", "line_type": "mobile"}
    )
    assert set(iter(result)) == {"carrier", "line_type"}


def test_get_returns_value_or_default() -> None:
    result = ValidationResult(is_valid=True, value="x", data={"carrier": "Dialog"})
    assert result.get("carrier") == "Dialog"
    assert result.get("missing") is None
    assert result.get("missing", "fallback") == "fallback"


def test_repr_uses_subclass_name() -> None:
    """``__repr__`` should reflect the actual class, not always 'ValidationResult'."""
    from helakit.phone import PhoneResult

    result = PhoneResult(is_valid=True, value="0712345678", normalized="+94712345678")
    assert repr(result).startswith("PhoneResult(")
