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
| Validate a whole column             | `validate_nic(df["nic"])`                          |
| Audit a DataFrame with cross-checks | `validate_nic(df, nic_col=..., dob_col=..., ...)`  |
| Batch → DataFrame of diagnostics    | `validate_nic(anything).to_pandas()`               |

## If you're coming from pandas

The batch API is designed to feel like the tools you already use. A
typical audit is three lines:

```python
import pandas as pd
from helakit import validate_nic

df = pd.read_csv("customers.csv")

batch = validate_nic(df["nic"])       # a Series works directly
df[batch.is_valid]                    # boolean-mask filtering, like df[mask]
batch.describe()                      # summary counts, like df.describe()
batch.to_pandas()                     # diagnostics as a DataFrame
```

Everything follows pandas conventions you already know:

| pandas habit                  | helakit equivalent                          |
| ----------------------------- | ------------------------------------------- |
| `df[mask]`                    | `df[batch.is_valid]`                        |
| `df.head()`                   | `batch.head()`                              |
| `df[:3]`                      | `batch[:3]`                                 |
| `df.describe()`               | `batch.describe()`                          |
| `df.to_dict("records")`       | `batch.to_dicts()`                          |
| `pd.to_numeric(errors="coerce")` | `validate_nic(..., errors="coerce")`, `convert_nic(..., errors="coerce")` |
| `Series.map(...)` column transforms | `df["nic_new"] = convert_nic(df["nic"], errors="coerce")` |

## `validate_nic`

The headline function. Accepts a single string or any batch
input — list, list-of-dicts, pandas/polars Series, or pandas/polars
DataFrame. Scalar input returns a `NicResult`; every batch shape
returns a `NICBatchResult`.

### Single NIC

```python
from helakit import validate_nic

result = validate_nic("820149894V")

result.is_valid          # True
result.normalized        # "820149894"  (V/X stripped, used for dedup)

# Decoded fields are one attribute away:
result.format            # "old"
result.dob               # datetime.date(1982, 1, 14)
result.gender            # "male"
result.age               # 44 (vs today, recomputed on each access)
result.age_at(date(2026, 1, 1))  # 43 (vs an explicit reference date)
result.year              # 1982
result.serial            # 989
result.voting_eligible   # True

# The same fields, bundled into one frozen dataclass:
result.decoded           # NICDecoded(format='old', dob=date(1982, 1, 14), ...)
result.to_dict()         # flat record dict — one row of to_pandas()
```

Properties return `None` on invalid results, so attribute access never
raises. `NicResult` is truthy when valid, so it drops into `if`
statements naturally:

```python
if result := validate_nic(user_input):
    print(result.dob)
else:
    for err in result.errors:
        print(err.code, err.message)
```

See **[Working with results](../concepts/results.md)** for the full
menu of access patterns (`result.dob`, `result["decoded"]`,
`result.get(...)`, `result.data`).

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
`validate_nic` and the `is_valid` mask.

## Batch input

`validate_nic` accepts five batch shapes. All of them return the same
`NICBatchResult`, so the reading code never changes when the input
shape does.

| Input shape           | Example                                       | Needs `nic_col`? |
| --------------------- | --------------------------------------------- | ---------------- |
| `list[str]`           | `validate_nic(["820149894V", ...])`           | no               |
| `list[dict]`          | `validate_nic(rows, nic_col="nic")`           | yes              |
| pandas/polars Series  | `validate_nic(df["nic"])`                     | no (not allowed) |
| pandas DataFrame      | `validate_nic(df, nic_col="nic")`             | yes              |
| polars DataFrame      | `validate_nic(df, nic_col="nic")`             | yes              |

### List of strings

```python
batch = validate_nic(["820149894V", "820149894X", "199201409894"])

batch.summary.valid              # 3
batch.summary.duplicate_groups   # 1   (the V and X stripped to the same key)
batch.duplicates                 # {"820149894": [0, 1]}

for result in batch:
    print(result.is_valid, result.normalized)
```

### Series (pandas or polars)

A Series is treated like a list of strings — no `nic_col` needed
(a Series has no columns, so passing `nic_col` raises
`InvalidInputError`):

```python
batch = validate_nic(df["nic"])

df[batch.is_valid]               # rows with valid NICs
batch.to_pandas()                # fresh frame of diagnostics
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

mismatch = batch[1]
mismatch.dob_match                # False
mismatch.gender_match             # False
mismatch.mismatch_reasons         # ["dob", "gender"]
mismatch.mismatch_detail
# "dob: NIC says 1982-01-14, supplied 1982-03-14;
#  gender: NIC says male, supplied female"
mismatch["dob_decoded"]           # date(1982, 1, 14)
mismatch["dob_supplied"]          # date(1982, 3, 14)
```

Accepted formats:

- **Gender:** `"M"`, `"F"`, `"Male"`, `"Female"`, `"MALE"`, `"FEMALE"`
  (case-insensitive). Anything else raises `InvalidInputError` (or is
  captured per-row with `errors="coerce"` — see below).
- **DOB:** `datetime.date`, `datetime.datetime`, ISO 8601 string
  (`"YYYY-MM-DD"`), or any object exposing `to_pydatetime()` (covers
  pandas Timestamp and numpy datetime64).
- Missing values (`None`, `NaN`, `pd.NaT`, polars `Null`) are treated
  as "no value supplied" — that row's match field stays unset rather
  than triggering a mismatch.

### pandas / polars DataFrames

Pass a DataFrame and helakit annotates a **copy** with diagnostic
columns (the original frame is never mutated). The copy is available
as `batch.df`, or equivalently `batch.to_pandas()` / `batch.to_polars()`:

```python
import pandas as pd
from helakit import validate_nic

df = pd.DataFrame({
    "nic":    ["820149894V", "820149894V", "199201409894", "garbage"],
    "dob":    ["1982-01-14", "1982-03-14", "1992-01-14",   None],
    "gender": ["M",          "F",          "Male",         None],
})

batch = validate_nic(df, nic_col="nic", dob_col="dob", gender_col="gender")
out = batch.to_pandas()   # your columns + the diagnostic columns below
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

pandas and polars are optional extras — install only what you need:

```bash
pip install helakit[pandas]   # or [polars], or [pandas,polars]
```

## The `NICBatchResult` container

Every batch call returns a `NICBatchResult`. It behaves like the
containers you already know — sized, iterable, indexable, sliceable —
and converts to tabular form on demand.

### Indexing, slicing, iteration

```python
batch = validate_nic(["820149894V", "garbage", "830250995X"])

len(batch)          # 3
batch[0]            # first NicResult
batch[:2]           # list of the first two, like df[:2]
batch.head(2)       # same thing, pandas-style
for r in batch: ...  # iterates NicResults in input order
```

### Filtering

```python
batch.is_valid      # [True, False, True] — row-aligned boolean mask
batch.valid         # [NicResult, NicResult] — only the clean rows
batch.invalid       # [NicResult] — only the failures

df[batch.is_valid]                      # pandas filtering
pl_df.filter(pl.Series(batch.is_valid)) # polars filtering
```

### Summarising

```python
batch.describe()              # NICSummary(total=3, valid=2, invalid=1, ...)
batch.describe().to_dict()    # plain dict, e.g. for pd.Series(...)
batch.summary                 # same object, attribute-style
bool(batch)                   # True only when *every* row is valid
```

`NICSummary` fields: `total`, `valid`, `invalid`, `duplicate_groups`,
`duplicate_rows`, `dob_mismatches`, `gender_mismatches`.

### Converting

```python
batch.to_dicts()     # list of flat record dicts — zero dependencies
batch.to_pandas()    # pandas DataFrame (needs helakit[pandas])
batch.to_polars()    # polars DataFrame (needs helakit[polars])
```

- For **DataFrame input**, `to_pandas()` / `to_polars()` return the
  annotated copy of your frame (all your columns preserved).
- For **every other input shape** (list, dicts, Series), they build a
  fresh frame with a `nic` column (the original values) plus the
  diagnostic columns from the table above.
- `to_dicts()` uses the same keys, so a record and a frame row always
  agree. A single `NicResult` flattens the same way via
  `result.to_dict()`.

### Duplicate detection

`batch.duplicates` maps each canonical NIC (uppercased, V/X suffix
stripped) to the row indices where it appears — only groups of two or
more are included. Because old and new formats normalise differently,
duplicates are detected *within* a format, and a reissued card with a
different voting letter (`...V` vs `...X`) still counts as the same
person:

```python
batch = validate_nic(["820149894V", "820149894X"])
batch.duplicates                  # {"820149894": [0, 1]}
batch.summary.duplicate_groups    # 1
batch.summary.duplicate_rows      # 2
```

## `convert_nic`

Old → new conversion. The reverse direction is not supported because
new NICs do not encode the V/X voting flag, so converting back would
lose information.

```python
from helakit import convert_nic

convert_nic("820149894V")     # "198201409894"
convert_nic("198201409894")   # "198201409894"  (valid new input is idempotent)
convert_nic("garbage")        # raises NICFormatError
convert_nic("199299999894")   # raises NICFormatError — 12 digits but an
                              # impossible day code; invalid input is never
                              # silently passed through
```

The mapping is: 2-digit year gets the century prefix (see
[Old-NIC century](#old-nic-century)), the 3-digit day code is kept
as-is, the 3-digit serial is zero-padded to 4 digits, and the check
digit carries over. `820149894V` → `1982` + `014` + `0989` + `4`.

`convert_nic` accepts the same batch shapes as `validate_nic`
(minus list-of-dicts): a list returns a list, a Series returns a
Series (index and name preserved), a DataFrame returns a copy with a
`nic_converted` column:

```python
convert_nic(["820149894V", "830250995X"])
# ["198201409894", "198302500995"]

df["nic_new"] = convert_nic(df["nic"], errors="coerce")   # Series in, Series out

out = convert_nic(df, nic_col="nic")                      # frame + nic_converted
```

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

Note the difference in scope: for `validate_nic` an unreadable **NIC**
never raises — it is always reported per-row — so `errors` only
concerns the cross-check inputs. For `convert_nic` the NIC itself is
the payload, so `errors` governs every value.

### Capturing failures in a separate column

For `convert_nic` on DataFrames, pass `error_col` to add a per-row
error-message column alongside `nic_converted`. It implies
`errors="coerce"` unless you set `errors` explicitly:

```python
out = convert_nic(df, nic_col="nic", error_col="nic_error")
out[["nic_converted", "nic_error"]]
#   nic_converted   nic_error
# 0 198201409894    None
# 1 None            Cannot convert 'garbage' — input is not a valid NIC (...)
```

`validate_nic` already exposes failures through the `nic_errors`
column on DataFrame output, so a separate `error_col` is unnecessary
there.

## Encoding details

### Anatomy of a NIC

```
Old:  82 014 989 4 V        New:  1982 014 0989 4
      │  │   │   │ │              │    │   │    │
      │  │   │   │ └ voting flag  │    │   │    └ check digit
      │  │   │   └ check digit    │    │   └ serial (4 digits)
      │  │   └ serial (3 digits)  │    └ day-of-year code
      │  └ day-of-year code       └ full birth year
      └ birth year (2 digits)
```

### Day-of-year

Both formats encode birth date as **day-of-year**, with female DOBs
offset by 500. So day codes 1–366 are male and 501–866 are female; the
parser strips the offset before decoding and reports the gender it
implies.

### Leap years

Sri Lankan NICs reserve **day 60 for February 29 in every year**, leap
or not. In a non-leap year day 60 is therefore a *phantom* date with no
real calendar equivalent and is reported as `nic.invalid_date`. Days
61–366 in non-leap years shift down by one to land on the correct
calendar date; for example **March 1 in 1983 encodes as day 61, not
day 60**, and day 366 in a non-leap year decodes to December 31.

### Check digit

The Department for Registration of Persons has not published the
modulo-11 check digit algorithm and no public implementation has
reverse-engineered it. Helakit extracts the digit (`decoded.check_digit`)
but does **not** verify it. Once the algorithm becomes available,
verification can be enabled without changing the public API.

### Age

Age is deliberately **not** stored on the result — it depends on the
current date, which the NIC does not encode. Read it through
`result.age` (recomputed against today on every access, never goes
stale) or `result.age_at(some_date)` (deterministic, testable).

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
