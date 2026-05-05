"""Tests for pandas and polars DataFrame integration.

These tests skip cleanly if the optional dependency isn't installed.
"""

from __future__ import annotations

from datetime import date

import pytest

from helakit import InvalidInputError, NICFormatError, convert_nic, validate_nic

pd = pytest.importorskip("pandas")
pl = pytest.importorskip("polars")


def test_pandas_validate_appends_columns() -> None:
    df = pd.DataFrame(
        {
            "nic": ["820149894V", "199201409894", "garbage"],
            "dob": ["1982-01-14", "1992-03-14", None],
            "gender": ["M", "F", None],
        }
    )
    batch = validate_nic(df, nic_col="nic", dob_col="dob", gender_col="gender")
    assert batch.df is not None
    expected_cols = {
        "nic_valid",
        "nic_normalized",
        "nic_format",
        "nic_decoded_dob",
        "nic_decoded_gender",
        "nic_dob_match",
        "nic_gender_match",
        "nic_mismatch_reasons",
        "nic_mismatch_detail",
        "nic_errors",
    }
    assert expected_cols.issubset(set(batch.df.columns))
    assert batch.df["nic_valid"].tolist() == [True, True, False]
    assert batch.df["nic_decoded_gender"].tolist()[:2] == ["male", "male"]


def test_pandas_does_not_mutate_input() -> None:
    df = pd.DataFrame({"nic": ["820149894V"]})
    validate_nic(df, nic_col="nic")
    assert "nic_valid" not in df.columns


def test_pandas_mismatch_detail_populated() -> None:
    df = pd.DataFrame(
        {
            "nic": ["820149894V"],
            "dob": ["1982-03-14"],
            "gender": ["F"],
        }
    )
    batch = validate_nic(df, nic_col="nic", dob_col="dob", gender_col="gender")
    detail = batch.df["nic_mismatch_detail"].iloc[0]
    assert "dob" in detail and "gender" in detail
    assert "1982-01-14" in detail and "1982-03-14" in detail


def test_pandas_missing_column_raises() -> None:
    df = pd.DataFrame({"nic": ["820149894V"]})
    with pytest.raises(InvalidInputError):
        validate_nic(df, nic_col="nic", dob_col="missing")


def test_pandas_validate_errors_coerce_survives_bad_row() -> None:
    df = pd.DataFrame(
        {
            "nic": ["820149894V", "820149894V", "199201409894"],
            "dob": ["1982-01-14", "not a date", "1992-03-14"],
            "gender": ["M", "alien", "F"],
        }
    )
    batch = validate_nic(df, nic_col="nic", dob_col="dob", gender_col="gender", errors="coerce")
    assert batch.df is not None
    assert batch.df["nic_valid"].tolist() == [True, False, True]
    bad_codes = batch.df["nic_errors"].tolist()[1]
    assert "nic.bad_dob_input" in bad_codes
    assert "nic.bad_gender_input" in bad_codes


def test_pandas_validate_default_errors_raise_on_bad_row() -> None:
    df = pd.DataFrame(
        {
            "nic": ["820149894V"],
            "dob": ["not a date"],
        }
    )
    with pytest.raises(InvalidInputError):
        validate_nic(df, nic_col="nic", dob_col="dob")


def test_pandas_handles_nan_dob() -> None:
    df = pd.DataFrame({"nic": ["820149894V"], "dob": [float("nan")]})
    batch = validate_nic(df, nic_col="nic", dob_col="dob")
    assert "dob_match" not in batch.results[0].data


def test_polars_validate_appends_columns() -> None:
    df = pl.DataFrame(
        {
            "nic": ["820149894V", "199201409894"],
            "dob": ["1982-01-14", "1992-03-14"],
            "gender": ["Male", "F"],
        }
    )
    batch = validate_nic(df, nic_col="nic", dob_col="dob", gender_col="gender")
    assert batch.df is not None
    out = batch.df
    assert out["nic_valid"].to_list() == [True, True]
    assert out["nic_dob_match"].to_list() == [True, False]


def test_polars_missing_column_raises() -> None:
    df = pl.DataFrame({"nic": ["820149894V"]})
    with pytest.raises(InvalidInputError):
        validate_nic(df, nic_col="nic", gender_col="missing")


def test_pandas_convert_appends_column() -> None:
    df = pd.DataFrame({"nic": ["820149894V", "830250995X"]})
    out = convert_nic(df, nic_col="nic")
    assert out["nic_converted"].tolist() == ["198201409894", "198302500995"]


def test_pandas_convert_propagates_invalid() -> None:
    df = pd.DataFrame({"nic": ["820149894V", "garbage"]})
    with pytest.raises(NICFormatError):
        convert_nic(df, nic_col="nic")


def test_pandas_convert_errors_coerce() -> None:
    df = pd.DataFrame({"nic": ["820149894V", "garbage", "830250995X"]})
    out = convert_nic(df, nic_col="nic", errors="coerce")
    converted = out["nic_converted"].tolist()
    assert converted[0] == "198201409894"
    assert pd.isna(converted[1])
    assert converted[2] == "198302500995"


def test_pandas_convert_errors_ignore() -> None:
    df = pd.DataFrame({"nic": ["820149894V", "garbage"]})
    out = convert_nic(df, nic_col="nic", errors="ignore")
    assert out["nic_converted"].tolist() == ["198201409894", "garbage"]


def test_pandas_convert_error_col_implies_coerce() -> None:
    df = pd.DataFrame({"nic": ["820149894V", "garbage"]})
    out = convert_nic(df, nic_col="nic", error_col="nic_error")
    converted = out["nic_converted"].tolist()
    assert converted[0] == "198201409894"
    assert pd.isna(converted[1])
    errors = out["nic_error"].tolist()
    assert pd.isna(errors[0])
    assert isinstance(errors[1], str) and "garbage" in errors[1]


def test_pandas_convert_error_col_with_explicit_ignore() -> None:
    df = pd.DataFrame({"nic": ["820149894V", "garbage"]})
    out = convert_nic(df, nic_col="nic", errors="ignore", error_col="nic_error")
    assert out["nic_converted"].tolist() == ["198201409894", "garbage"]
    assert pd.isna(out["nic_error"].iloc[0])
    assert "garbage" in out["nic_error"].iloc[1]


def test_pandas_convert_does_not_mutate_input() -> None:
    df = pd.DataFrame({"nic": ["820149894V", "garbage"]})
    convert_nic(df, nic_col="nic", errors="coerce", error_col="nic_error")
    assert "nic_converted" not in df.columns
    assert "nic_error" not in df.columns


def test_pandas_convert_accepts_series() -> None:
    series = pd.Series(["820149894V", "830250995X"], name="nic")
    out = convert_nic(series, errors="coerce")
    assert isinstance(out, pd.Series)
    assert out.tolist() == ["198201409894", "198302500995"]
    assert out.name == "nic"


def test_pandas_convert_series_assigns_back_to_frame() -> None:
    """Regression: df[col] = convert_nic(df[col], ...) must not trip
    pandas' "Columns must be same length as key" by returning a frame.
    """
    df = pd.DataFrame({"nic": ["820149894V", "garbage", "830250995X"]})
    df["nic_new"] = convert_nic(df["nic"], errors="coerce")
    assert df["nic_new"].iloc[0] == "198201409894"
    assert pd.isna(df["nic_new"].iloc[1])
    assert df["nic_new"].iloc[2] == "198302500995"


def test_pandas_convert_series_preserves_index() -> None:
    series = pd.Series(["820149894V", "830250995X"], index=[10, 20], name="nic")
    out = convert_nic(series, errors="coerce")
    assert out.index.tolist() == [10, 20]


def test_pandas_convert_series_rejects_nic_col() -> None:
    series = pd.Series(["820149894V"], name="nic")
    with pytest.raises(InvalidInputError):
        convert_nic(series, nic_col="nic")


def test_pandas_convert_series_rejects_error_col() -> None:
    series = pd.Series(["820149894V"], name="nic")
    with pytest.raises(InvalidInputError):
        convert_nic(series, error_col="nic_error")


def test_polars_convert_appends_column() -> None:
    df = pl.DataFrame({"nic": ["820149894V"]})
    out = convert_nic(df, nic_col="nic")
    assert out["nic_converted"].to_list() == ["198201409894"]


def test_polars_convert_accepts_series() -> None:
    series = pl.Series("nic", ["820149894V", "garbage", "830250995X"])
    out = convert_nic(series, errors="coerce")
    assert isinstance(out, pl.Series)
    assert out.to_list() == ["198201409894", None, "198302500995"]
    assert out.name == "nic"


def test_polars_convert_series_rejects_nic_col() -> None:
    series = pl.Series("nic", ["820149894V"])
    with pytest.raises(InvalidInputError):
        convert_nic(series, nic_col="nic")


def test_polars_convert_series_rejects_error_col() -> None:
    series = pl.Series("nic", ["820149894V"])
    with pytest.raises(InvalidInputError):
        convert_nic(series, error_col="nic_error")


def test_polars_convert_requires_nic_col() -> None:
    df = pl.DataFrame({"nic": ["820149894V"]})
    with pytest.raises(InvalidInputError):
        convert_nic(df)


def test_polars_convert_errors_coerce() -> None:
    df = pl.DataFrame({"nic": ["820149894V", "garbage"]})
    out = convert_nic(df, nic_col="nic", errors="coerce")
    assert out["nic_converted"].to_list() == ["198201409894", None]


def test_polars_convert_error_col_populated() -> None:
    df = pl.DataFrame({"nic": ["820149894V", "garbage"]})
    out = convert_nic(df, nic_col="nic", error_col="nic_error")
    assert out["nic_converted"].to_list() == ["198201409894", None]
    errors = out["nic_error"].to_list()
    assert errors[0] is None
    assert isinstance(errors[1], str) and "garbage" in errors[1]


def test_pandas_decoded_dob_is_real_date() -> None:
    df = pd.DataFrame({"nic": ["820149894V"]})
    batch = validate_nic(df, nic_col="nic")
    decoded_dob = batch.df["nic_decoded_dob"].iloc[0]
    assert decoded_dob == date(1982, 1, 14)
