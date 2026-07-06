"""Tests for batch validation: lists, list-of-dicts, cross-checking."""

from __future__ import annotations

from datetime import date

import pytest

from helakit import InvalidInputError, NICBatchResult, validate_nic


def test_list_of_strings() -> None:
    batch = validate_nic(["820149894V", "199201409894", "garbage"])
    assert isinstance(batch, NICBatchResult)
    assert len(batch) == 3
    assert batch.summary.total == 3
    assert batch.summary.valid == 2
    assert batch.summary.invalid == 1


def test_year_zero_row_does_not_abort_batch() -> None:
    # A single malformed row (year 0 → invalid date) must not raise and abort
    # the whole batch; it is reported as one invalid result alongside the rest.
    batch = validate_nic(["199201409894", "000020000018"])
    assert batch.summary.total == 2
    assert batch.summary.valid == 1
    assert batch.summary.invalid == 1


def test_duplicate_detection_strips_v_x() -> None:
    batch = validate_nic(["820149894V", "820149894X", "199201409894"])
    assert batch.summary.duplicate_groups == 1
    assert batch.duplicates == {"820149894": [0, 1]}


def test_no_duplicates_reported_for_unique_inputs() -> None:
    batch = validate_nic(["820149894V", "199201409894"])
    assert batch.duplicates == {}
    assert batch.summary.duplicate_groups == 0


def test_list_of_dicts_cross_check_match() -> None:
    rows = [
        {"nic": "820149894V", "dob": "1982-01-14", "gender": "M"},
        {"nic": "820149894V", "dob": "1982-01-14", "gender": "Male"},
    ]
    batch = validate_nic(rows, nic_col="nic", dob_col="dob", gender_col="gender")
    for r in batch.results:
        assert r.data["dob_match"] is True
        assert r.data["gender_match"] is True
        assert r.data["mismatch_reasons"] == []


def test_list_of_dicts_cross_check_mismatch() -> None:
    rows = [{"nic": "820149894V", "dob": "1982-03-14", "gender": "F"}]
    batch = validate_nic(rows, nic_col="nic", dob_col="dob", gender_col="gender")
    r = batch.results[0]
    assert r.data["dob_match"] is False
    assert r.data["gender_match"] is False
    assert set(r.data["mismatch_reasons"]) == {"dob", "gender"}
    assert r.data["dob_supplied"] == date(1982, 3, 14)
    assert r.data["dob_decoded"] == date(1982, 1, 14)
    assert r.data["gender_supplied"] == "female"
    assert r.data["gender_decoded"] == "male"
    detail = r.data["mismatch_detail"]
    assert "1982-01-14" in detail
    assert "1982-03-14" in detail
    assert "male" in detail
    assert "female" in detail
    assert batch.summary.dob_mismatches == 1
    assert batch.summary.gender_mismatches == 1


def test_partial_cross_check_dob_only() -> None:
    rows = [{"nic": "820149894V", "dob": "1982-01-14"}]
    batch = validate_nic(rows, nic_col="nic", dob_col="dob")
    r = batch.results[0]
    assert r.data["dob_match"] is True
    assert "gender_match" not in r.data


def test_gender_accepts_full_word_uppercase() -> None:
    rows = [{"nic": "820149894V", "gender": "MALE"}]
    batch = validate_nic(rows, nic_col="nic", gender_col="gender")
    assert batch.results[0].data["gender_match"] is True


def test_gender_invalid_value_raises() -> None:
    rows = [{"nic": "820149894V", "gender": "other"}]
    with pytest.raises(InvalidInputError):
        validate_nic(rows, nic_col="nic", gender_col="gender")


def test_dob_accepts_iso_string_and_date() -> None:
    rows = [
        {"nic": "820149894V", "dob": "1982-01-14"},
        {"nic": "820149894V", "dob": date(1982, 1, 14)},
    ]
    batch = validate_nic(rows, nic_col="nic", dob_col="dob")
    assert all(r.data["dob_match"] for r in batch.results)


def test_dob_unparseable_raises() -> None:
    rows = [{"nic": "820149894V", "dob": "not a date"}]
    with pytest.raises(InvalidInputError):
        validate_nic(rows, nic_col="nic", dob_col="dob")


def test_missing_dob_skips_check() -> None:
    rows = [{"nic": "820149894V", "dob": None}]
    batch = validate_nic(rows, nic_col="nic", dob_col="dob")
    assert "dob_match" not in batch.results[0].data


def test_list_of_dict_requires_nic_col() -> None:
    with pytest.raises(InvalidInputError):
        validate_nic([{"x": "820149894V"}])


def test_unsupported_input_type_raises() -> None:
    with pytest.raises(InvalidInputError):
        validate_nic(12345)  # type: ignore[arg-type]


def test_iteration() -> None:
    batch = validate_nic(["820149894V", "199201409894"])
    valid_count = sum(1 for r in batch if r.is_valid)
    assert valid_count == 2


def test_indexing() -> None:
    batch = validate_nic(["820149894V", "garbage"])
    assert batch[0].is_valid
    assert not batch[1].is_valid


def test_batch_result_truthy_when_all_valid() -> None:
    assert bool(validate_nic(["820149894V"])) is True
    assert bool(validate_nic(["garbage"])) is False


def test_batch_handles_non_string_input() -> None:
    batch = validate_nic([{"nic": 12345}], nic_col="nic")
    assert not batch.results[0].is_valid
    assert batch.results[0].errors[0].code == "nic.not_a_string"


def test_errors_coerce_captures_bad_gender_per_row() -> None:
    rows = [
        {"nic": "820149894V", "gender": "M"},
        {"nic": "820149894V", "gender": "other"},
        {"nic": "820149894V", "gender": "F"},
    ]
    batch = validate_nic(rows, nic_col="nic", gender_col="gender", errors="coerce")
    assert batch.results[0].is_valid
    assert not batch.results[1].is_valid
    bad_codes = [e.code for e in batch.results[1].errors]
    assert "nic.bad_gender_input" in bad_codes
    # Third row should still process even though row 2 was bad.
    assert batch.results[2].data["gender_match"] is False


def test_errors_coerce_captures_bad_dob_per_row() -> None:
    rows = [
        {"nic": "820149894V", "dob": "not a date"},
        {"nic": "820149894V", "dob": "1982-01-14"},
    ]
    batch = validate_nic(rows, nic_col="nic", dob_col="dob", errors="coerce")
    assert not batch.results[0].is_valid
    codes = [e.code for e in batch.results[0].errors]
    assert "nic.bad_dob_input" in codes
    assert batch.results[1].data["dob_match"] is True


def test_errors_coerce_captures_both_dob_and_gender() -> None:
    rows = [{"nic": "820149894V", "dob": "bogus", "gender": "alien"}]
    batch = validate_nic(rows, nic_col="nic", dob_col="dob", gender_col="gender", errors="coerce")
    codes = {e.code for e in batch.results[0].errors}
    assert {"nic.bad_dob_input", "nic.bad_gender_input"} <= codes


def test_errors_invalid_value_rejected() -> None:
    with pytest.raises(InvalidInputError):
        validate_nic(["820149894V"], errors="silently-fail")  # type: ignore[arg-type]


def test_errors_raise_default_still_propagates() -> None:
    rows = [{"nic": "820149894V", "gender": "other"}]
    with pytest.raises(InvalidInputError):
        validate_nic(rows, nic_col="nic", gender_col="gender")


# --- pandas-style container API ------------------------------------------


def test_slicing_returns_list() -> None:
    batch = validate_nic(["820149894V", "199201409894", "garbage"])
    first_two = batch[:2]
    assert isinstance(first_two, list)
    assert len(first_two) == 2
    assert first_two[0].is_valid


def test_head_mirrors_dataframe_head() -> None:
    batch = validate_nic(["820149894V", "199201409894", "garbage"])
    assert len(batch.head(2)) == 2
    assert len(batch.head()) == 3  # fewer rows than the default 5


def test_is_valid_mask_is_row_aligned() -> None:
    batch = validate_nic(["820149894V", "garbage", "199201409894"])
    assert batch.is_valid == [True, False, True]


def test_valid_and_invalid_filters() -> None:
    batch = validate_nic(["820149894V", "garbage"])
    assert [r.value for r in batch.valid] == ["820149894V"]
    assert [r.value for r in batch.invalid] == ["garbage"]


def test_describe_returns_summary() -> None:
    batch = validate_nic(["820149894V", "garbage"])
    summary = batch.describe()
    assert summary is batch.summary
    assert summary.to_dict() == {
        "total": 2,
        "valid": 1,
        "invalid": 1,
        "duplicate_groups": 0,
        "duplicate_rows": 0,
        "dob_mismatches": 0,
        "gender_mismatches": 0,
    }


def test_to_dicts_produces_flat_records() -> None:
    batch = validate_nic(["820149894V", "garbage"])
    records = batch.to_dicts()
    assert len(records) == 2
    good, bad = records
    assert good["nic"] == "820149894V"
    assert good["nic_valid"] is True
    assert good["nic_normalized"] == "820149894"
    assert good["nic_format"] == "old"
    assert good["nic_errors"] is None
    assert bad["nic_valid"] is False
    assert bad["nic_errors"] == "nic.bad_length"


def test_to_dicts_includes_cross_check_columns() -> None:
    rows = [{"nic": "820149894V", "dob": "1982-03-14", "gender": "F"}]
    batch = validate_nic(rows, nic_col="nic", dob_col="dob", gender_col="gender")
    record = batch.to_dicts()[0]
    assert record["nic_dob_match"] is False
    assert record["nic_gender_match"] is False
    assert record["nic_mismatch_reasons"] == "dob,gender"


def test_result_to_dict_matches_record_fields() -> None:
    result = validate_nic("820149894V")
    record = result.to_dict()
    assert tuple(record) == type(result).record_fields()


def test_batch_repr_shows_counts() -> None:
    batch = validate_nic(["820149894V", "garbage"])
    assert repr(batch) == "NICBatchResult(total=2, valid=1, invalid=1, duplicate_groups=0)"
