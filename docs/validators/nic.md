# NIC

Sri Lanka issues a National Identity Card (NIC) number that encodes the
holder's date of birth, gender, and (on old-format cards) voting eligibility.
Helakit supports **both** formats:

- **Old** — 9 digits + a `V` or `X` suffix (e.g. `820149894V`). Issued
  before 2016. The trailing letter is the voting flag: `V` for eligible,
  `X` for not eligible.
- **New** — 12 fully numeric digits (e.g. `198201409894`). Issued from
  2016 onwards.

## Quick reference

| What you want                       | Call                                               |
| ----------------------------------- | -------------------------------------------------- |
| Validate one NIC and decode it      | `validate_nic("820149894V")`                       |
| Yes/no check                        | `is_valid_nic("820149894V")`                       |
| Old → new format                    | `convert_nic("820149894V")`                        |
| Audit a list / DataFrame            | `validate_nic(df, nic_col=..., dob_col=..., ...)`  |

## `validate_nic`

The headline function. Accepts a single string or any batch
input — list, list-of-dicts, pandas DataFrame, or polars DataFrame.

### Single NIC

```python
from helakit import validate_nic

result = validate_nic("820149894V")

result.is_valid          # True
result.normalized        # "820149894"  (V/X stripped, used for dedup)
result.data["decoded"]   # NICDecoded(...)

decoded = result.data["decoded"]
decoded.format           # "old"
decoded.dob              # datetime.date(1982, 1, 14)
decoded.gender           # "male"
decoded.age              # 44 (computed at call time)
decoded.voting_eligible  # True
decoded.serial           # 989
decoded.check_digit      # 4
```

`ValidationResult` is truthy when `is_valid` is `True`, so the rich
form drops into `if` statements naturally:

```python
if result := validate_nic(user_input):
    print(result.data["decoded"].dob)
else:
    for err in result.errors:
        print(err.code, err.message)
```

### Restricting the format

```python
validate_nic("820149894V", format="old")    # passes
validate_nic("820149894V", format="new")    # rejected with nic.format_mismatch
```

### Old-NIC century

Old NICs encode only the last two digits of the birth year. Helakit
defaults to **1900s** because the format was retired in 2016 and almost
every old NIC in circulation belongs to a 20th-century birth. If you
have a known cohort that goes the other way, override it:

```python
validate_nic("100149894V", century=2000)
# decoded.year == 2010
```

### Boolean shorthand

```python
from helakit import is_valid_nic

is_valid_nic("820149894V")                  # True
is_valid_nic("garbage")                     # False
is_valid_nic("820149894V", format="new")    # False
```

`is_valid_nic` is **scalar-only**. For batch checks, use
`validate_nic` and inspect each result.

## `convert_nic`

Old → new conversion. The reverse direction is not supported because
new NICs do not encode the V/X voting flag.

```python
from helakit import convert_nic

convert_nic("820149894V")     # "198201409894"
convert_nic("198201409894")   # "198201409894"  (idempotent)
convert_nic("garbage")        # raises NICFormatError
```

For lists and DataFrames see the **Batch input** section below.

## Batch input

`validate_nic` and `convert_nic` accept four batch shapes; the return
type follows the input shape.

### List of strings

```python
batch = validate_nic(["820149894V", "820149894X", "199201409894"])

batch.summary.valid              # 3
batch.summary.duplicate_groups   # 1   (the V and X stripped to the same key)
batch.duplicates                 # {"820149894": [0, 1]}

for result in batch:
    print(result.is_valid, result.normalized)
```

### List of dicts (with cross-checking)

When you supply `dob_col` and/or `gender_col`, helakit cross-checks the
decoded NIC fields against your supplied values and records any
mismatch in detail.

```python
rows = [
    {"nic": "820149894V", "dob": "1982-01-14", "gender": "M"},
    {"nic": "820149894V", "dob": "1982-03-14", "gender": "F"},
]

batch = validate_nic(
    rows,
    nic_col="nic",
    dob_col="dob",
    gender_col="gender",
)

batch.summary.dob_mismatches      # 1
batch.summary.gender_mismatches   # 1

mismatch = batch.results[1].data
mismatch["mismatch_reasons"]      # ["dob", "gender"]
mismatch["mismatch_detail"]
# "dob: NIC says 1982-01-14, supplied 1982-03-14;
#  gender: NIC says male, supplied female"
mismatch["dob_decoded"]           # date(1982, 1, 14)
mismatch["dob_supplied"]          # date(1982, 3, 14)
```

Accepted formats:

- **Gender:** `"M"`, `"F"`, `"Male"`, `"Female"`, `"MALE"`, `"FEMALE"`
  (case-insensitive). Anything else raises `InvalidInputError`.
- **DOB:** `datetime.date`, `datetime.datetime`, ISO 8601 string
  (`"YYYY-MM-DD"`), or any object exposing `to_pydatetime()` (covers
  pandas Timestamp and numpy datetime64).
- Missing values (`None`, `NaN`, `pd.NaT`, polars `Null`) are treated
  as "no value supplied" — that row's match field stays unset rather
  than triggering a mismatch.

### pandas / polars DataFrames

Pass a DataFrame and helakit returns a copy with diagnostic columns
appended. The original frame is never mutated.

```python
import pandas as pd
from helakit import validate_nic

df = pd.DataFrame({
    "nic":    ["820149894V", "820149894V", "199201409894", "garbage"],
    "dob":    ["1982-01-14", "1982-03-14", "1992-01-14",   None],
    "gender": ["M",          "F",          "Male",         None],
})

batch = validate_nic(df, nic_col="nic", dob_col="dob", gender_col="gender")
batch.df  # copy of df with the columns below appended
```

| Column                 | Meaning                                                            |
| ---------------------- | ------------------------------------------------------------------ |
| `nic_valid`            | `True` if the NIC parsed cleanly.                                  |
| `nic_normalized`       | Canonical form (uppercase, V/X stripped). Use for dedup.           |
| `nic_format`           | `"old"` / `"new"` / `None`.                                        |
| `nic_decoded_dob`      | Date decoded from the NIC.                                         |
| `nic_decoded_gender`   | `"male"` / `"female"` / `None`.                                    |
| `nic_dob_match`        | `True` / `False` / `None` (skipped when no `dob_col`).             |
| `nic_gender_match`     | Same idea.                                                         |
| `nic_mismatch_reasons` | Comma-joined list: `"dob"`, `"gender"`, or `"dob,gender"`.         |
| `nic_mismatch_detail`  | Human-readable string showing supplied vs decoded values.          |
| `nic_errors`           | Comma-joined error codes for invalid rows.                         |

`pyproject.toml` keeps pandas and polars as optional extras. Install
them only if you need DataFrame support:

```bash
pip install helakit[pandas]   # or [polars], or [pandas,polars]
```

`convert_nic` works the same way — pass a DataFrame and `nic_col` and
get a frame back with a `nic_converted` column. By default, conversion
is strict and an invalid value raises `NICFormatError`. See
**Lenient batch handling** below for `errors="coerce"` and `error_col`.

## Lenient batch handling

By default both batch entry points fail loudly the moment they hit a
value they cannot interpret — `convert_nic` raises `NICFormatError`,
and `validate_nic` raises `InvalidInputError` on a bad cross-check
`dob` / `gender`. That is the right behaviour when bad data is a bug
in your pipeline, but a hassle when you are auditing a real-world
file with the usual smattering of typos.

Pass `errors="coerce"` (mirrors `pandas.to_numeric`) to keep going:

```python
from helakit import convert_nic, validate_nic

# Single bad row no longer kills the whole batch.
convert_nic(["820149894V", "garbage", "830250995X"], errors="coerce")
# ["198201409894", None, "198302500995"]

convert_nic(df, nic_col="nic", errors="coerce")
# garbage rows get None in nic_converted

# Same idea, but keep the original string instead of None:
convert_nic(df, nic_col="nic", errors="ignore")
```

`validate_nic` accepts `errors="raise"` (default) and `errors="coerce"`.
Coerce mode catches unparseable `dob` / `gender` values and turns them
into per-row `nic.bad_dob_input` / `nic.bad_gender_input` errors:

```python
df = pd.DataFrame({
    "nic":    ["820149894V", "820149894V", "199201409894"],
    "dob":    ["1982-01-14", "not a date", "1992-03-14"],
    "gender": ["M",          "alien",      "F"],
})

batch = validate_nic(
    df,
    nic_col="nic",
    dob_col="dob",
    gender_col="gender",
    errors="coerce",
)
batch.summary.invalid          # 1
batch.df["nic_errors"].iloc[1] # "nic.bad_dob_input,nic.bad_gender_input"
```

### Capturing failures in a separate column

For `convert_nic` on DataFrames, pass `error_col` to add a per-row
error-message column alongside `nic_converted`. It implies
`errors="coerce"` unless you set `errors` explicitly:

```python
out = convert_nic(df, nic_col="nic", error_col="nic_error")
out[["nic_converted", "nic_error"]]
#   nic_converted   nic_error
# 0 198201409894    None
# 1 None            Cannot convert 'garbage' — input is not a valid old NIC (...)
```

`validate_nic` already exposes failures through the `nic_errors`
column on DataFrame output, so a separate `error_col` is unnecessary
there.

## Encoding details

### Day-of-year

Both formats encode birth date as **day-of-year**, with female DOBs
offset by 500. So day codes 1–366 are male and 501–866 are female; the
parser strips the offset before decoding.

### Leap years

Sri Lankan NICs reserve **day 60 for February 29 in every year**, leap
or not. In a non-leap year day 60 is therefore a *phantom* date with no
real calendar equivalent and is reported as `nic.invalid_date`. Days
61–366 in non-leap years shift down by one to land on the correct
calendar date; for example **March 1 in 1982 encodes as day 61, not
day 60**.

### Check digit

The Department for Registration of Persons has not published the
modulo-11 check digit algorithm and no public implementation has
reverse-engineered it. Helakit extracts the digit (`decoded.check_digit`)
but does **not** verify it. Once the algorithm becomes available,
verification can be enabled without changing the public API.

## Errors

Validation failures are reported via `result.errors` — a list of
[`ValidationError`][helakit.ValidationError] objects. Programmer errors
(wrong input type, unparseable gender, etc.) raise
[`InvalidInputError`][helakit.InvalidInputError].

| Error code            | Meaning                                                  |
| --------------------- | -------------------------------------------------------- |
| `nic.bad_length`      | Input was not 10 (old) or 12 (new) characters.           |
| `nic.non_numeric`     | Digits expected but got letters elsewhere than V/X.      |
| `nic.bad_suffix`      | Old NIC didn't end in `V` or `X`.                        |
| `nic.bad_day_code`    | Day-of-year encoding was outside 1-366 / 501-866.        |
| `nic.invalid_date`    | Day code does not yield a real date in the given year.   |
| `nic.format_mismatch` | Format hint (`old` / `new`) didn't match the input.      |
| `nic.not_a_string`    | A row in a batch supplied a non-string NIC.              |
| `nic.bad_dob_input`   | Cross-check `dob` was unparseable; only emitted with `errors="coerce"`. |
| `nic.bad_gender_input`| Cross-check `gender` was unparseable; only emitted with `errors="coerce"`. |
