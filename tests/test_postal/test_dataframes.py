"""Tests for postal-code validation over pandas and polars objects."""

from __future__ import annotations

import pytest

from helakit import InvalidInputError, PostalResult, validate_postal

pd = pytest.importorskip("pandas")
pl = pytest.importorskip("polars")

CODES = ["10250", "80000", "99999"]
DISTRICTS = ["Colombo", "Matara", "Galle"]

DIAGNOSTIC_COLUMNS = [c for c in PostalResult.record_fields() if c != "postal"]


# ---- pandas ---------------------------------------------------------------


def test_pandas_dataframe_is_annotated_in_place_of_a_copy() -> None:
    df = pd.DataFrame({"code": CODES})
    batch = validate_postal(df, postal_col="code")
    out = batch.to_pandas()
    assert list(df.columns) == ["code"], "the caller's frame is not mutated"
    assert list(out.columns) == ["code", *DIAGNOSTIC_COLUMNS]
    assert out["postal_post_office"].tolist()[:2] == ["Nugegoda", "Galle"]
    assert out["postal_valid"].tolist() == [True, True, False]


def test_pandas_to_pandas_returns_the_annotated_frame() -> None:
    df = pd.DataFrame({"code": CODES})
    batch = validate_postal(df, postal_col="code")
    assert batch.to_pandas() is batch.df


def test_pandas_mask_filters_the_original_frame() -> None:
    df = pd.DataFrame({"code": CODES})
    batch = validate_postal(df, postal_col="code")
    assert df[batch.is_valid]["code"].tolist() == ["10250", "80000"]


def test_pandas_district_cross_check() -> None:
    df = pd.DataFrame({"code": CODES, "district": DISTRICTS})
    out = validate_postal(df, postal_col="code", district_col="district").to_pandas()
    assert out["postal_district_match"].tolist() == [True, False, None]


def test_pandas_series_is_treated_as_a_list() -> None:
    series = pd.Series(CODES)
    batch = validate_postal(series)
    assert batch.is_valid == [True, True, False]
    assert batch.df is None


def test_pandas_series_rejects_column_names() -> None:
    with pytest.raises(InvalidInputError, match="does not apply to Series input"):
        validate_postal(pd.Series(CODES), postal_col="code")


def test_pandas_missing_column() -> None:
    df = pd.DataFrame({"code": CODES})
    with pytest.raises(InvalidInputError, match="not found in DataFrame"):
        validate_postal(df, postal_col="nope")


def test_pandas_requires_a_column_name() -> None:
    with pytest.raises(InvalidInputError, match="postal_col is required"):
        validate_postal(pd.DataFrame({"code": CODES}))


def test_pandas_nulls_become_row_errors() -> None:
    df = pd.DataFrame({"code": ["10250", None]})
    out = validate_postal(df, postal_col="code").to_pandas()
    assert out["postal_errors"].tolist()[1] == "postal.not_a_string"


def test_pandas_empty_frame() -> None:
    df = pd.DataFrame({"code": pd.Series([], dtype="object")})
    batch = validate_postal(df, postal_col="code")
    assert len(batch) == 0
    assert list(batch.to_pandas().columns) == ["code", *DIAGNOSTIC_COLUMNS]


# ---- polars ---------------------------------------------------------------


def test_polars_dataframe_is_annotated() -> None:
    df = pl.DataFrame({"code": CODES})
    out = validate_postal(df, postal_col="code").to_polars()
    assert out.columns == ["code", *DIAGNOSTIC_COLUMNS]
    assert out["postal_district"].to_list() == ["Colombo", "Galle", None]


def test_polars_to_polars_returns_the_annotated_frame() -> None:
    df = pl.DataFrame({"code": CODES})
    batch = validate_postal(df, postal_col="code")
    assert batch.to_polars() is batch.df


def test_polars_district_cross_check() -> None:
    df = pl.DataFrame({"code": CODES, "district": DISTRICTS})
    out = validate_postal(df, postal_col="code", district_col="district").to_polars()
    assert out["postal_district_match"].to_list() == [True, False, None]


def test_polars_series_is_treated_as_a_list() -> None:
    batch = validate_postal(pl.Series("code", CODES))
    assert batch.is_valid == [True, True, False]
    assert batch.df is None


def test_polars_missing_column() -> None:
    with pytest.raises(InvalidInputError, match="not found in DataFrame"):
        validate_postal(pl.DataFrame({"code": CODES}), postal_col="nope")


# ---- conversions across input shapes --------------------------------------


def test_list_input_converts_to_pandas() -> None:
    out = validate_postal(CODES).to_pandas()
    assert list(out.columns) == list(PostalResult.record_fields())
    assert out["postal"].tolist() == CODES


def test_list_input_converts_to_polars() -> None:
    out = validate_postal(CODES).to_polars()
    assert out.columns == list(PostalResult.record_fields())
    assert out["postal_valid"].to_list() == [True, True, False]


def test_polars_input_converts_to_pandas() -> None:
    out = validate_postal(pl.DataFrame({"code": CODES}), postal_col="code").to_pandas()
    assert list(out.columns) == list(PostalResult.record_fields())


def test_pandas_input_converts_to_polars() -> None:
    out = validate_postal(pd.DataFrame({"code": CODES}), postal_col="code").to_polars()
    assert out.columns == list(PostalResult.record_fields())


def test_summary_survives_a_round_trip_to_pandas() -> None:
    df = pd.DataFrame({"code": CODES})
    batch = validate_postal(df, postal_col="code")
    assert pd.Series(batch.describe().to_dict())["valid"] == 2
