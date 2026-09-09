"""Tests for postal-code batch validation and the pandas-style container."""

from __future__ import annotations

import pytest

from helakit import (
    InvalidInputError,
    PostalBatchResult,
    PostalResult,
    PostalSummary,
    validate_postal,
)

CODES = ["10250", "80000", "99999", "10250"]


# ---- Container behaviour --------------------------------------------------


def test_list_input_returns_a_batch() -> None:
    batch = validate_postal(CODES)
    assert isinstance(batch, PostalBatchResult)
    assert len(batch) == 4
    assert all(isinstance(r, PostalResult) for r in batch)


def test_is_valid_is_a_row_aligned_mask() -> None:
    assert validate_postal(CODES).is_valid == [True, True, False, True]


def test_valid_and_invalid_partitions() -> None:
    batch = validate_postal(CODES)
    assert [r.normalized for r in batch.valid] == ["10250", "80000", "10250"]
    assert [r.value for r in batch.invalid] == ["99999"]


def test_integer_and_slice_indexing() -> None:
    batch = validate_postal(CODES)
    assert batch[0].post_office == "Nugegoda"
    assert [r.value for r in batch[:2]] == ["10250", "80000"]
    assert batch[-1].post_office == "Nugegoda"


def test_head_defaults_to_five() -> None:
    batch = validate_postal(CODES)
    assert len(batch.head()) == 4
    assert len(batch.head(2)) == 2


def test_batch_is_truthy_only_when_every_row_is_valid() -> None:
    assert not validate_postal(CODES)
    assert validate_postal(["10250", "80000"])


def test_repr_reports_the_summary() -> None:
    assert "total=4" in repr(validate_postal(CODES))
    assert "duplicate_groups=1" in repr(validate_postal(CODES))


def test_empty_input() -> None:
    batch = validate_postal([])
    assert len(batch) == 0
    assert batch.describe().total == 0
    assert bool(batch) is True


# ---- Summary --------------------------------------------------------------


def test_describe_returns_the_summary() -> None:
    batch = validate_postal(CODES)
    assert isinstance(batch.describe(), PostalSummary)
    assert batch.describe() is batch.summary
    assert batch.describe().to_dict() == {
        "total": 4,
        "valid": 3,
        "invalid": 1,
        "duplicate_groups": 1,
        "duplicate_rows": 2,
        "district_mismatches": 0,
    }


def test_duplicates_are_indexed_by_code() -> None:
    assert validate_postal(CODES).duplicates == {"10250": [0, 3]}


def test_invalid_rows_never_count_as_duplicates() -> None:
    batch = validate_postal(["99999", "99999"])
    assert batch.duplicates == {}
    assert batch.describe().duplicate_groups == 0


def test_tuple_input_is_accepted() -> None:
    assert validate_postal(("10250", "80000")).describe().valid == 2


# ---- list-of-dicts and cross-checking -------------------------------------


def test_list_of_dicts_requires_a_column_name() -> None:
    with pytest.raises(InvalidInputError, match="postal_col is required"):
        validate_postal([{"code": "10250"}])


def test_list_of_dicts() -> None:
    batch = validate_postal([{"code": "10250"}, {"code": "99999"}], postal_col="code")
    assert batch.is_valid == [True, False]


def test_district_cross_check_matches() -> None:
    rows = [{"code": "10250", "d": "Colombo"}]
    result = validate_postal(rows, postal_col="code", district_col="d")[0]
    assert result.district_match is True
    assert result.mismatch_reasons == []
    assert result.mismatch_detail is None
    assert result.is_valid


def test_district_cross_check_accepts_short_codes_and_any_case() -> None:
    rows = [{"code": "10250", "d": "cmb"}, {"code": "10250", "d": "  colombo "}]
    batch = validate_postal(rows, postal_col="code", district_col="d")
    assert [r.district_match for r in batch] == [True, True]


def test_district_mismatch_is_reported_but_not_fatal() -> None:
    rows = [{"code": "80000", "d": "Matara"}]
    result = validate_postal(rows, postal_col="code", district_col="d")[0]
    assert result.is_valid, "a mismatch is a data-quality signal, not a bad code"
    assert result.district_match is False
    assert result.mismatch_reasons == ["district"]
    assert "Matara" in (result.mismatch_detail or "")
    assert "Galle" in (result.mismatch_detail or "")


def test_district_mismatches_are_counted() -> None:
    rows = [
        {"code": "80000", "d": "Matara"},
        {"code": "10250", "d": "Colombo"},
        {"code": "99999", "d": "Colombo"},
    ]
    batch = validate_postal(rows, postal_col="code", district_col="d")
    assert batch.describe().district_mismatches == 1


def test_missing_district_values_skip_the_cross_check() -> None:
    rows = [{"code": "10250", "d": None}]
    result = validate_postal(rows, postal_col="code", district_col="d")[0]
    assert result.district_match is None
    assert result.mismatch_reasons is None


# ---- errors="raise" / "coerce" --------------------------------------------


def test_unparseable_district_raises_by_default() -> None:
    rows = [{"code": "10250", "d": "Atlantis"}]
    with pytest.raises(InvalidInputError, match="Unrecognised district"):
        validate_postal(rows, postal_col="code", district_col="d")


def test_unparseable_district_coerces_to_a_row_error() -> None:
    rows = [{"code": "10250", "d": "Atlantis"}, {"code": "80000", "d": "Galle"}]
    batch = validate_postal(rows, postal_col="code", district_col="d", errors="coerce")
    assert batch.is_valid == [False, True]
    assert [e.code for e in batch[0].errors] == ["postal.bad_district_input"]
    assert batch[1].district_match is True


def test_non_string_district_raises() -> None:
    rows = [{"code": "10250", "d": 7}]
    with pytest.raises(InvalidInputError, match="District must be a string"):
        validate_postal(rows, postal_col="code", district_col="d")


def test_non_string_district_coerces() -> None:
    rows = [{"code": "10250", "d": 7}]
    batch = validate_postal(rows, postal_col="code", district_col="d", errors="coerce")
    assert [e.code for e in batch[0].errors] == ["postal.bad_district_input"]


def test_non_string_rows_are_flagged_not_raised() -> None:
    batch = validate_postal([{"code": None}, {"code": 10250}], postal_col="code")
    assert batch.is_valid == [False, False]
    assert [e.code for e in batch[0].errors] == ["postal.not_a_string"]


# ---- to_dicts -------------------------------------------------------------


def test_to_dicts_is_dependency_free() -> None:
    records = validate_postal(["10250", "99999"]).to_dicts()
    assert [r["postal_valid"] for r in records] == [True, False]
    assert records[0]["postal_province"] == "Western"
    assert records[1]["postal_errors"] == "postal.unknown_code"
    assert tuple(records[0]) == PostalResult.record_fields()
