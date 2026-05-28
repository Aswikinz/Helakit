# Getting Started

This page takes you from an empty environment to a working call in a
couple of minutes. For a deeper tour of what comes back from a
validator, see [Working with results](concepts/results.md).

## Installation

=== "pip"

    ```bash
    pip install helakit
    ```

=== "uv"

    ```bash
    uv add helakit
    ```

=== "poetry"

    ```bash
    poetry add helakit
    ```

Helakit supports Python 3.10 and newer and has **no runtime
dependencies** — installing it adds nothing to your dependency tree
beyond the package itself.

The optional extras enable DataFrame batch validation:

```bash
pip install "helakit[pandas]"          # or [polars], or [pandas,polars]
```

!!! tip "Editor support"
    Helakit ships a `py.typed` marker. PyCharm, VS Code (Pylance),
    and mypy will all see the typed properties on `NicResult`,
    `PhoneResult`, and `PostalResult` and autocomplete them.

## Two ways to validate

Every validator ships in two flavours: a rich one that returns a result
object, and a boolean shorthand.

### Rich result (recommended)

```python
from helakit import validate_phone

result = validate_phone("0712345678")

if result.is_valid:
    print(result.normalized)   # "+94712345678"
    print(result.carrier)      # "Mobitel"
    print(result.line_type)    # "mobile"
else:
    for err in result.errors:
        print(err.code, err.message)
```

The result is also **truthy when valid**, so you can skip `.is_valid`
in `if` statements:

```python
if validate_phone(x):
    ...
```

### Boolean shorthand

```python
from helakit import is_valid_phone

is_valid_phone("0712345678")  # True
is_valid_phone("0001234567")  # False
```

Use the rich form when you need parsed fields or precise error
reporting; use the shorthand when you only need a yes/no.

## Four ways to read a field

Helakit's results support every access pattern you might already be
using elsewhere. They all read the same data — pick whichever fits the
surrounding code.

```python
result = validate_phone("0712345678")

result.carrier            # 1. typed attribute access (preferred)
result["carrier"]         # 2. dict-style access (pandas/dict feel)
result.get("carrier")     # 3. safe access with optional default
result.data["carrier"]    # 4. underlying dict for power users
```

| Pattern | Returns when missing | Type-checked? |
| ------- | -------------------- | ------------- |
| `result.carrier` | `None` | ✅ |
| `result["carrier"]` | raises `KeyError` | ❌ (always `Any`) |
| `result.get("carrier", default)` | `default` (or `None`) | ❌ |
| `result.data["carrier"]` | raises `KeyError` | ❌ |

The typed attribute form is the recommended one — it never raises on
invalid results, returning `None` instead.

## A complete example

```python
from helakit import validate_phone

numbers = [
    "0712345678",          # valid mobile
    "+94 81 234 5678",     # valid fixed-line, international form
    "07ABCDEFGH",          # invalid characters
    "0001234567",          # invalid prefix
]

for n in numbers:
    result = validate_phone(n)
    if result:
        print(f"{n:25}  ✓ {result.carrier} ({result.line_type})")
    else:
        codes = ", ".join(e.code for e in result.errors)
        print(f"{n:25}  ✗ {codes}")
```

Output:

```text
0712345678                 ✓ Mobitel (mobile)
+94 81 234 5678            ✓ SLT (fixed)
07ABCDEFGH                 ✗ phone.invalid_characters
0001234567                 ✗ phone.unknown_prefix
```

## Where to go next

- **[NIC validator](validators/nic.md)** — parse old (`820149894V`) and
  new (`198201409894`) NICs, extract date of birth, gender, and voting
  eligibility, and batch-validate lists or DataFrames.
- **[Phone validator](validators/phone.md)** — every option, every error
  code, every prefix table.
- **[Working with results](concepts/results.md)** — `ValidationResult`,
  the typed subclasses, and the four access patterns in detail.
- **[Error handling](concepts/errors.md)** — every error code, what
  causes it, and how to react.
