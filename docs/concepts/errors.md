# Error handling

Helakit splits errors into two categories:

- **Validation failures** — the input is wrong (bad characters, wrong
  length, unknown prefix, …). These come back as a normal
  `ValidationResult` with `is_valid=False` and one or more
  `ValidationError`s in `errors`.
- **Programmer errors** — the *call* is wrong (passing `None` where a
  string is required). These are raised as exceptions.

The rule of thumb: if you have data from a user, a file, or a database,
you don't need `try/except`. If you have a bug, you do.

## `ValidationError`

Every validation failure is reported as a `ValidationError` — a frozen
dataclass with three fields.

```python
@dataclass(frozen=True, slots=True)
class ValidationError:
    code: str           # stable, machine-readable id
    message: str        # human-readable description
    field: str | None   # which field of the input failed
```

```python
result = validate_phone("0001234567")
err = result.errors[0]

err.code     # "phone.unknown_prefix"
err.message  # "Prefix '000' is not a recognised Sri Lankan network prefix."
err.field    # "value"
```

!!! tip "Match on `code`, not `message`"
    Codes are stable across releases. Messages are not — they may be
    rephrased for clarity at any time. Always branch on `err.code` in
    code; reserve `err.message` for surfacing to end users.

## Idiomatic handling

A `match` statement on the error code reads cleanly when you need to
react differently to different failures.

```python
result = validate_phone(user_input)
if not result:
    match result.errors[0].code:
        case "phone.invalid_characters":
            return "Please enter digits only."
        case "phone.unknown_prefix":
            return "Doesn't look like a Sri Lankan number."
        case "phone.invalid_length" | "phone.missing_prefix":
            return "Expected 10 digits, e.g. 0712345678."
        case _:
            return result.errors[0].message
```

If you don't need branching, the whole error list collapses to a single
log line nicely:

```python
codes = ", ".join(e.code for e in result.errors)
logger.warning("Phone rejected: %s (%s)", user_input, codes)
```

## All error codes

Codes are namespaced by validator.

### Phone

| Code | Triggered by |
| ---- | ------------ |
| `phone.invalid_characters` | Non-digit characters (other than a leading `+`), including Unicode digits and an empty string. |
| `phone.missing_prefix` | Input has no leading `0`, `+94`, or `94`. |
| `phone.invalid_length` | After normalising to local form, length is not 10. |
| `phone.unknown_prefix` | First 3 digits of the local form are not a recognised Sri Lankan prefix. |

See [Phone › Error codes](../validators/phone.md#error-codes) for
worked examples of each.

### NIC

| Code | Triggered by |
| ---- | ------------ |
| `nic.bad_length` | Input is not 10 (old) or 12 (new) characters. |
| `nic.non_numeric` | Digits expected but got letters elsewhere than V/X. |
| `nic.bad_suffix` | Old NIC didn't end in `V` or `X`. |
| `nic.bad_day_code` | Day-of-year encoding was outside 1-366 / 501-866. |
| `nic.invalid_date` | Day code does not yield a real date in the given year. |
| `nic.format_mismatch` | `format=` hint (`"old"` / `"new"`) didn't match the input. |
| `nic.not_a_string` | A row in a batch supplied a non-string NIC. |
| `nic.bad_dob_input` | Cross-check `dob` was unparseable; only emitted with `errors="coerce"`. |
| `nic.bad_gender_input` | Cross-check `gender` was unparseable; only emitted with `errors="coerce"`. |

See [NIC › Errors](../validators/nic.md#errors) for context on each.

### Postal (planned)

| Code | Triggered by |
| ---- | ------------ |
| `postal.invalid_length` | Not exactly 5 characters. |
| `postal.invalid_characters` | Contains non-digit characters. |
| `postal.unknown_code` | Five digits but not a code in our table. |

## Exceptions

Helakit's exception hierarchy is small:

```text
HelakitError
├── InvalidInputError    # wrong type passed to a validator
├── PhoneError           # reserved for phone-specific programmer errors
├── NICError             # NIC-specific programmer errors
│   └── NICFormatError   # convert_nic raises this on unconvertable input
└── PostalError          # reserved for postal-specific programmer errors
```

All exceptions inherit from `HelakitError`, so a single
`except HelakitError` catches anything Helakit raises.

### `InvalidInputError`

Raised when you call a validator with something that isn't a string,
or pass an unparseable cross-check value in batch mode with
`errors="raise"` (the default).

```python
from helakit import InvalidInputError, validate_phone

try:
    validate_phone(None)
except InvalidInputError as e:
    print(e)  # "validate_phone requires a string; got NoneType."
```

You don't need to wrap normal validator calls in `try/except` — the
only way to get an `InvalidInputError` is to pass the wrong type.

### `NICFormatError`

Raised by `convert_nic` when its input cannot be parsed as either NIC
format, or parses but fails validation (for example a 12-digit input
encoding an impossible birth date). Conversion has no sensible result
object to return — failure must propagate as an exception. In batch
mode, pass `errors="coerce"` to capture the failure inline instead.

```python
from helakit import NICFormatError, convert_nic

try:
    convert_nic("garbage")
except NICFormatError as e:
    ...

# Or stay non-fatal:
convert_nic(["820149894V", "garbage"], errors="coerce")
# ["198201409894", None]
```

### Domain-specific exception classes

`PhoneError`, `NICError`, and `PostalError` are reserved for
domain-specific programmer errors. `NICFormatError` is the only one
that's live today. You can write `except PhoneError` now — the code
will keep working if a phone-specific programmer error becomes a thing
in a future release.

## When *not* to use `try/except`

```python
# ❌ Wrong: wrapping a validator call
try:
    result = validate_phone(user_input)
except Exception:
    handle_error()

# ✅ Right: check the result
result = validate_phone(user_input)
if not result:
    handle_error(result.errors)
```

Bad phone numbers are a normal outcome, not an exceptional one. The
exception path is reserved for programmer errors. Mixing the two
patterns hides genuine bugs.
