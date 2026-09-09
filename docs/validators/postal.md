# Postal

The postal validator resolves a Sri Lankan five-digit postal code to the
post office it names, the district that post office sits in, and the
province the district belongs to. It is backed by a transcription of the
Department of Posts *Sri Lanka Postal Code Directory* — **2,121 codes**
covering all 25 districts.

## Quick start

```python
from helakit import validate_postal, is_valid_postal

result = validate_postal("10250")

result.is_valid  # True
result.normalized  # "10250"
result.post_office  # "Nugegoda"
result.district  # "Colombo"
result.province  # "Western"
result.sub_post  # False

is_valid_postal("10250")  # True
```

`validate_postal` returns a [`PostalResult`](#postalresult), a
[`ValidationResult`](../concepts/results.md) subclass with typed
properties for every field the validator extracts.

## What "valid" means

A postal code is considered valid when *all* of the following hold:

1. After stripping whitespace and hyphens, the string contains **only
   ASCII digits**.
2. There are **exactly five** of them.
3. The five digits are **a code in the Department of Posts directory**.

Rule 3 is what makes this more than a regex: `12345` is five digits and
still invalid, because no post office carries that code.

Codes below `10000` keep their leading zeros. Colombo 07 is `"00700"`,
not `"700"` — the latter is reported as `postal.invalid_length`.

## Accepted input forms

Whitespace and hyphens are stripped before validation; everything else is
strict.

```python
validate_postal("10250")  # canonical
validate_postal("  10250  ")  # surrounding whitespace
validate_postal("102 50")  # internal spaces
validate_postal("102-50")  # hyphens
```

All four return `normalized == "10250"`. The original string is always
preserved on `result.value`, so you can echo the user's input back
unchanged.

## Reading the result

The same four access styles work as for every other helakit validator:

```python
result = validate_postal("10250")

# 1. Typed attribute access (preferred — autocomplete + type checks)
result.district

# 2. Dict-style — useful if the field name is dynamic
result["district"]

# 3. Safe access with default
result.get("district", "unknown")

# 4. The underlying dict, for power users
result.data["district"]
```

### Available fields

| Field | Type | Example |
| ----- | ---- | ------- |
| `post_office` | `str \| None` | `"Nugegoda"` |
| `district` | `str \| None` | `"Colombo"` |
| `province` | `str \| None` | `"Western"` |
| `district_code` | `str \| None` | `"CMB"` |
| `province_code` | `str \| None` | `"WP"` |
| `sub_post` | `bool \| None` | `False` |
| `decoded` | `PostalDecoded \| None` | all of the above, bundled |

Every property returns `None` on an invalid result, so attribute access
never raises. Guard with `if result:` before reading.

Two further properties — `district_match` and `mismatch_reasons` — are
populated only when you cross-check a district column in batch mode. See
[Cross-checking a district column](#cross-checking-a-district-column).

## Error codes

The validator short-circuits on the first hard failure, so a scalar call
returns at most one error.

### `postal.invalid_characters`

Anything that is not an ASCII digit once whitespace and hyphens are
stripped — including an empty string and Unicode digits.

```python
validate_postal("abcde").errors[0].code  # "postal.invalid_characters"
validate_postal("1025O").errors[0].code  # letter O, not zero
validate_postal("").errors[0].code
```

### `postal.invalid_length`

All digits, but not exactly five of them. The message reminds you about
leading zeros, which is the usual cause.

```python
validate_postal("700").errors[0].code  # "postal.invalid_length"
validate_postal("102500").errors[0].code
```

### `postal.unknown_code`

Five digits that are not in the directory.

```python
validate_postal("99999").errors[0].code  # "postal.unknown_code"
```

### `postal.not_a_string`

Batch-only. A row supplied something other than a string — a `None`, a
`NaN`, or a number, which is what pandas gives you when a postal-code
column was read as integers. The row is flagged; the batch continues.

### `postal.bad_district_input`

Batch-only, and only with `errors="coerce"`. The cross-check district
value could not be interpreted. With the default `errors="raise"` an
unparseable district raises `InvalidInputError` instead.

### Reacting to errors

```python
result = validate_postal(user_input)

if not result:
    code = result.errors[0].code
    if code == "postal.unknown_code":
        show("That is not a Sri Lankan postal code.")
    elif code == "postal.invalid_length":
        show("Postal codes are five digits — remember the leading zeros.")
    else:
        show(result.errors[0].message)
```

Match on `code`, never on `message`. Codes are stable across releases;
messages are not.

## Exceptions

Bad *data* comes back as an invalid result. Bad *code* raises:

```python
validate_postal(10250)  # InvalidInputError — pass a string
validate_postal(df)  # InvalidInputError — postal_col is required
validate_postal(df, postal_col="nope")  # InvalidInputError — no such column
validate_postal(["10250"], errors="x")  # InvalidInputError — bad errors mode
```

`PostalError` exists for postal-specific programmer errors and is
exported for forward compatibility; nothing raises it today.

## Batch input

Like [`validate_nic`](nic.md#batch-input), `validate_postal` accepts a
whole column and returns a
[`PostalBatchResult`](#the-postalbatchresult-container) instead of a
single result.

### List of strings

```python
batch = validate_postal(["10250", "80000", "99999"])

len(batch)  # 3
batch.is_valid  # [True, True, False]
batch[0].post_office  # "Nugegoda"
```

### Series (pandas or polars)

A Series is treated like a list of strings — it has no columns, so
`postal_col` does not apply and passing it raises.

```python
import pandas as pd

df = pd.DataFrame({"code": ["10250", "80000", "99999"]})
batch = validate_postal(df["code"])

df[batch.is_valid]  # keep only the rows with real codes
```

### DataFrames

Pass the frame and name the column. The result's `df` is a **copy** of
your frame with helakit's diagnostic columns appended — your original is
never mutated.

```python
df = pd.DataFrame({"code": ["10250", "80000", "99999"]})
out = validate_postal(df, postal_col="code").to_pandas()

list(out.columns)
# ['code', 'postal_valid', 'postal_normalized', 'postal_post_office',
#  'postal_district', 'postal_province', 'postal_sub_post',
#  'postal_district_match', 'postal_mismatch_detail', 'postal_errors']
```

polars works identically via `to_polars()`.

### Cross-checking a district column

If your table already carries a district, hand it over and helakit will
tell you where the two disagree. A mismatch is a *data-quality signal*,
not an invalid code — the row stays valid.

```python
df = pd.DataFrame(
    {
        "code": ["10250", "80000"],
        "district": ["Colombo", "Matara"],
    }
)
batch = validate_postal(df, postal_col="code", district_col="district")

batch[0].district_match  # True
batch[1].district_match  # False — 80000 is Galle, not Matara
batch[1].mismatch_detail  # "district: supplied 'Matara', code says 'Galle'"
batch.describe().district_mismatches  # 1
```

The district column accepts either the short code (`"CMB"`) or the full
name (`"Colombo"`), in any letter case.

### Lenient batch handling

By default an uninterpretable district aborts the whole batch, matching
strict pandas semantics. Pass `errors="coerce"` to record it as a per-row
error instead:

```python
rows = [{"code": "10250", "district": "Atlantis"}]

validate_postal(rows, postal_col="code", district_col="district")
# InvalidInputError: Unrecognised district value 'Atlantis'.

batch = validate_postal(rows, postal_col="code", district_col="district", errors="coerce")
batch[0].errors[0].code  # "postal.bad_district_input"
```

## The `PostalBatchResult` container

It behaves like the pandas containers you already know.

### Indexing, slicing, iteration

```python
batch[0]  # one PostalResult
batch[:3]  # list of the first three
batch.head(2)  # same idea, mirroring DataFrame.head
for result in batch:  # iterates rows in input order
    ...
bool(batch)  # True only when every row is valid
```

### Filtering

```python
batch.valid  # list[PostalResult] that passed
batch.invalid  # list[PostalResult] that failed
batch.is_valid  # row-aligned list[bool] — feed it to df[...]
```

### Summarising

```python
batch.describe().to_dict()
# {'total': 3, 'valid': 2, 'invalid': 1, 'duplicate_groups': 0,
#  'duplicate_rows': 0, 'district_mismatches': 0}
```

### Converting

`to_pandas()`, `to_polars()`, and `to_dicts()` all work regardless of
what shape the input was. `to_dicts()` needs no optional dependencies.

```python
validate_postal(["10250"]).to_dicts()
# [{'postal': '10250', 'postal_valid': True, 'postal_normalized': '10250',
#   'postal_post_office': 'Nugegoda', 'postal_district': 'Colombo',
#   'postal_province': 'Western', 'postal_sub_post': False,
#   'postal_district_match': None, 'postal_mismatch_detail': None,
#   'postal_errors': None}]
```

### Duplicate detection

Repeated codes are grouped by code and reported by row index.

```python
batch = validate_postal(["10250", "80000", "10250"])
batch.duplicates  # {'10250': [0, 2]}
batch.describe().duplicate_groups  # 1
```

Invalid rows never participate in duplicate groups.

## The code table

2,121 codes: 592 main post offices and 1,529 sub post offices. They break
down by province as follows.

| Province | Codes |
| -------- | ----- |
| Central | 331 |
| North Western | 308 |
| Western | 289 |
| Southern | 245 |
| Sabaragamuwa | 234 |
| Uva | 211 |
| North Central | 202 |
| Eastern | 158 |
| Northern | 143 |

The first two digits broadly track region — `00`–`12` Western, `20`–`22`
Central, `30`–`32` Eastern, `40`–`43` Northern, `50`–`51` North Central,
`60`–`61` North Western, `70`–`71` Sabaragamuwa, `80`–`82` Southern,
`90`–`91` Uva — but the mapping is not exact and helakit never infers a
district from the prefix. A few offices genuinely carry a code from a
neighbouring block; every lookup goes through the table.

Corrections and additions are welcome: the table is a plain dict in
`src/helakit/postal/_data.py`. Cite a source in the pull request.

## Recipes

### Flag bad codes in a spreadsheet

```python
out = validate_postal(df, postal_col="code").to_pandas()
out[~out["postal_valid"]][["code", "postal_errors"]]
```

### Fill in district and province from a code column

```python
out = validate_postal(df, postal_col="code").to_pandas()
df["district"] = out["postal_district"]
df["province"] = out["postal_province"]
```

### Audit an address table for district mismatches

```python
batch = validate_postal(df, postal_col="code", district_col="district")
suspect = [r for r in batch if r.district_match is False]

for result in suspect:
    print(result.value, result.mismatch_detail)
```

### Group customers by province

```python
out = validate_postal(df, postal_col="code").to_pandas()
out.groupby("postal_province").size()
```

## `PostalResult`

::: helakit.postal.PostalResult
    options:
      show_root_heading: false
      show_signature: false
      members: false

## `PostalDecoded`

::: helakit.postal.PostalDecoded
    options:
      show_root_heading: false
      show_signature: false
      members: false

## `PostalBatchResult`

::: helakit.postal.PostalBatchResult
    options:
      show_root_heading: false
      show_signature: false
      members: false

## `PostalSummary`

::: helakit.postal.PostalSummary
    options:
      show_root_heading: false
      show_signature: false
      members: false
