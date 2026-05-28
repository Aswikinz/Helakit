# Phone

The phone validator parses, normalizes, and decodes Sri Lankan phone
numbers. Given any input string, it tells you whether the number is
valid, what the canonical form is, who the carrier is, and whether it's
a mobile or fixed-line number.

## Quick start

```python
from helakit import validate_phone, is_valid_phone

result = validate_phone("0712345678")

result.is_valid       # True
result.normalized     # "+94712345678"
result.carrier        # "Mobitel"
result.line_type      # "mobile"
result.local          # "0712345678"

is_valid_phone("0712345678")  # True
```

`validate_phone` returns a [`PhoneResult`](#phoneresult), a
[`ValidationResult`](../concepts/results.md) subclass with typed
properties for every field the validator extracts.

## What "valid" means

A Sri Lankan phone number is considered valid when *all* of the
following hold:

1. The string contains **only ASCII digits**, optionally preceded by a
   `+`. Spaces, hyphens, and parentheses are tolerated and stripped.
2. The number can be coerced into a **10-digit local form**
   (`0XXXXXXXXX`) — either it already is one, or it's in international
   form (`+94XXXXXXXXX` or `94XXXXXXXXX`) and can be converted.
3. The leading 3 digits of the local form are a **recognised Sri Lankan
   mobile or fixed-line prefix** (the full table is in [Recognised
   prefixes](#recognised-prefixes) below).

If any check fails, the result is invalid and `errors` contains one
[`ValidationError`](../concepts/errors.md) explaining which rule was
broken. The validator short-circuits on the first hard failure, so you
will see at most one error per call today.

## Accepted input forms

The validator is permissive about whitespace and punctuation: spaces,
hyphens, and parentheses are stripped before validation. It is strict
about everything else.

=== "Local form"

    ```python
    validate_phone("0712345678").is_valid       # True
    validate_phone("071 234 5678").is_valid     # True
    validate_phone("071-234-5678").is_valid     # True
    validate_phone("(071) 234-5678").is_valid   # True
    ```

=== "International, with +"

    ```python
    validate_phone("+94712345678").is_valid     # True
    validate_phone("+94 71 234 5678").is_valid  # True
    ```

=== "International, without +"

    ```python
    validate_phone("94712345678").is_valid      # True
    ```

=== "Rejected"

    ```python
    validate_phone("712345678")     # missing leading 0 / country code
    validate_phone("07ABCDEFGH")    # non-digit characters
    validate_phone("٠٧١٢٣٤٥٦٧٨")    # Unicode (Arabic-Indic) digits
    validate_phone("07+12345678")   # '+' anywhere but the start
    ```

!!! warning "Unicode digits are rejected on purpose"
    Although Python's `str.isdigit()` returns `True` for
    Arabic-Indic and other Unicode digits, those characters mean
    different things in different locales. The validator only accepts
    `[0-9]` to avoid surprising round-trips through `int()` and
    database storage.

## Reading the result

A `PhoneResult` supports four equivalent access patterns. They all read
the same underlying data — pick whichever fits the surrounding code.

```python
result = validate_phone("0712345678")

# 1. Typed attribute access (preferred — autocomplete + type checks)
result.carrier            # "Mobitel"
result.line_type          # "mobile"
result.local              # "0712345678"
result.decoded            # PhoneDecoded(carrier='Mobitel', ...)

# 2. Dict-style — useful if the field name is dynamic
result["carrier"]         # "Mobitel"

# 3. Safe access with default
result.get("carrier", "Unknown")

# 4. The underlying dict, for power users
result.data["carrier"]
```

`result.carrier` returns `None` on an invalid result; `result["carrier"]`
raises `KeyError`. See [Working with results](../concepts/results.md)
for the full comparison table.

### Available fields

| Property | Type | Description |
| -------- | ---- | ----------- |
| `is_valid` | `bool` | Whether the number passed every check. |
| `value` | `str` | The original input, unmodified. |
| `normalized` | `str \| None` | Canonical `"+94XXXXXXXXX"` form. `None` if invalid. |
| `carrier` | `str \| None` | Network operator name (e.g. `"Mobitel"`). |
| `line_type` | `"mobile" \| "fixed" \| None` | Line classification. |
| `local` | `str \| None` | 10-digit local form (`"0XXXXXXXXX"`). |
| `decoded` | `PhoneDecoded \| None` | All three fields above bundled. |
| `errors` | `list[ValidationError]` | Empty when valid. |
| `data` | `dict[str, Any]` | Raw payload behind the typed properties. |

## Error codes

The phone validator can return one of four error codes. They are stable
across releases — match on `err.code`, not on `err.message`.

### `phone.invalid_characters`

The input contains a character other than ASCII digits or a leading
`+`. Triggered by letters, internal `+`, Unicode digits, special
characters, and empty strings.

```python
result = validate_phone("07ABCDEFGH")
result.errors[0].code     # "phone.invalid_characters"
result.errors[0].message  # "Phone number must contain digits only ..."
```

### `phone.missing_prefix`

The input is otherwise clean but does not start with `0` (local), `+94`
(international with `+`), or `94` (international without `+`).

```python
result = validate_phone("712345678")
result.errors[0].code  # "phone.missing_prefix"
```

### `phone.invalid_length`

The input has the right shape but the wrong number of digits. The local
form must be exactly 10 digits.

```python
result = validate_phone("071234567")    # 9 digits
result.errors[0].code  # "phone.invalid_length"

result = validate_phone("07123456789")  # 11 digits
result.errors[0].code  # "phone.invalid_length"
```

### `phone.unknown_prefix`

The three-digit local prefix (e.g. `"071"`, `"011"`) is not a recognised
Sri Lankan mobile or fixed-line prefix. This is the most useful error
in practice — it catches well-formed numbers that simply aren't valid
SL numbers.

```python
result = validate_phone("0001234567")
result.errors[0].code  # "phone.unknown_prefix"
```

### Reacting to errors

A `match` statement on the error code is the idiomatic way to branch on
why a number failed.

```python
result = validate_phone(user_input)
if not result:
    match result.errors[0].code:
        case "phone.invalid_characters":
            ask_user_to_re_enter()
        case "phone.unknown_prefix":
            ask_if_foreign_number()
        case "phone.invalid_length" | "phone.missing_prefix":
            show_format_hint()
```

For the complete list of error codes used across all validators, see
[Error handling](../concepts/errors.md).

## Exceptions

`validate_phone` and `is_valid_phone` raise — rather than return an
invalid result — for **programmer errors**:

| Exception | When |
| --------- | ---- |
| `helakit.InvalidInputError` | `value` is not a string (e.g. `None`, `int`). |

Bad data (a malformed phone number) is **not** an exception — it comes
back as a normal invalid result. Reserve `try/except` for the
programmer-error case.

```python
from helakit import InvalidInputError, validate_phone

try:
    validate_phone(None)
except InvalidInputError as e:
    ...  # caller passed the wrong type
```

## Recognised prefixes

The validator recognises the following three-digit local prefixes. The
data lives in `helakit.phone._data` and is sourced from the
Telecommunications Regulatory Commission of Sri Lanka (TRCSL).

=== "Mobile"

    | Prefix | Carrier |
    | ------ | ------- |
    | `070`, `076`, `077` | Dialog |
    | `074` | Dialog (special) |
    | `071`, `072` | Mobitel |
    | `075` | Airtel |
    | `078` | Hutch |
    | `079` | Lanka Bell |

=== "Fixed-line"

    | Prefix | City / Region |
    | ------ | ------------- |
    | `011` | Colombo (SLT / Dialog) |
    | `031` | Negombo |
    | `032` | Kurunegala |
    | `033` | Gampaha |
    | `034` | Kalutara |
    | `035` | Kegalle |
    | `036` | Avissawella |
    | `037` | Kurunegala (alt) |
    | `038` | Panadura |
    | `041` | Galle |
    | `045` | Ratnapura |
    | `047` | Hambantota |
    | `051`, `052` | Nuwara Eliya / Kandy |
    | `054` | Matale |
    | `055` | Badulla |
    | `057` | Bandarawela |
    | `063` | Ampara |
    | `065` | Batticaloa |
    | `066` | Polonnaruwa |
    | `067` | Kalmunai |
    | `081` | Kandy |
    | `091` | Galle (alt) |

!!! info "Found a missing prefix?"
    Prefix lists change occasionally as new operators are licensed.
    Please [open an issue](https://github.com/Aswikinz/Helakit/issues)
    or PR if you spot one that's missing or misclassified.

## Recipes

### Validate a column of numbers (pandas)

```python
import pandas as pd
from helakit import validate_phone

df = pd.DataFrame({"phone": ["0712345678", "94772345678", "bogus"]})

results = df["phone"].map(validate_phone)
df["is_valid"]   = results.map(bool)
df["normalized"] = results.map(lambda r: r.normalized)
df["carrier"]    = results.map(lambda r: r.carrier)
df["line_type"]  = results.map(lambda r: r.line_type)
```

### Filter to mobile numbers only

```python
mobile_numbers = [n for n in numbers if (r := validate_phone(n)) and r.line_type == "mobile"]
```

### Normalize for storage

```python
def normalize(n: str) -> str | None:
    """Return the canonical +94 form, or None if not a valid SL number."""
    result = validate_phone(n)
    return result.normalized if result else None
```

## `PhoneResult`

::: helakit.phone.PhoneResult
    options:
      show_root_heading: false
      show_signature: false
      members: false

## `PhoneDecoded`

::: helakit.phone.PhoneDecoded
    options:
      show_root_heading: false
      show_signature: false
      members: false
