# Working with results

Every validator in Helakit returns a `ValidationResult` — either the
base class itself or a domain-specific subclass like `NicResult`,
`PhoneResult`, or `PostalResult`. This page covers what's on a result,
how to read fields out of it, and how the typed subclasses give you
autocomplete without giving up the flexibility of a plain dict.

## The shape of a result

A `ValidationResult` has five attributes — every validator populates the
same five regardless of domain.

| Attribute | Type | When set |
| --------- | ---- | -------- |
| `is_valid` | `bool` | Always. `True` only if every check passed. |
| `value` | `str` | Always. The original input, unmodified. |
| `normalized` | `str \| None` | Set when valid. Canonical form of `value`. |
| `errors` | `list[ValidationError]` | Empty when valid; one or more entries otherwise. |
| `data` | `dict[str, Any]` | Extracted fields. Populated when valid. |

```python
from helakit import validate_phone

result = validate_phone("0712345678")
result.is_valid      # True
result.value         # "0712345678"
result.normalized    # "+94712345678"
result.errors        # []
result.data          # {'carrier': 'Mobitel', 'line_type': 'mobile', ...}
```

`ValidationResult` is a **frozen dataclass** — you cannot mutate a
result after the validator returns it.

## Truthiness

A result is truthy when valid and falsy when not, so you rarely need to
write `.is_valid`:

```python
if validate_phone(x):
    ...           # x is valid

result = validate_phone(x)
if not result:
    handle(result.errors)
```

## Four ways to read a field

Helakit supports every access pattern you might already be using. They
all read the same underlying `data` dict — pick whichever fits the
surrounding code.

```python
result = validate_phone("0712345678")

result.carrier            # 1. typed attribute access (preferred)
result["carrier"]         # 2. dict-style — pandas/dict feel
result.get("carrier")     # 3. safe access with optional default
result.data["carrier"]    # 4. underlying dict
```

The four patterns differ in two ways: what they return on a missing
field, and whether the IDE / mypy can type-check the access.

| Pattern | Returns when missing | IDE/mypy typed? |
| ------- | -------------------- | --------------- |
| `result.carrier` | `None` | ✅ |
| `result["carrier"]` | raises `KeyError` | ❌ (always `Any`) |
| `result.get("carrier", default)` | `default` (or `None`) | ❌ |
| `result.data["carrier"]` | raises `KeyError` | ❌ |

### When to use each

- **`result.carrier`** — your default. Fast to type, never raises,
  autocompleted by your editor, and checked by mypy.
- **`result["carrier"]`** — pick this when the field name is dynamic
  (`result[column_name]`), when you want a hard fail on a missing
  field, or simply when it reads better next to dict / DataFrame code.
- **`result.get("carrier", default)`** — when you need a non-`None`
  default. Equivalent to `result.carrier or default` but slightly
  clearer for booleans / numerics where `or` would also swallow falsy
  values.
- **`result.data["carrier"]`** — escape hatch if you need to iterate
  over every extracted field, or to copy the whole payload somewhere.

## Domain-specific result classes

`validate_phone`, `validate_nic`, and `validate_postal` each return a
subclass of `ValidationResult` that adds typed properties for the
fields it extracts.

| Validator | Returns | Typed properties |
| --------- | ------- | ---------------- |
| `validate_phone` | `PhoneResult` | `carrier`, `line_type`, `local`, `decoded` |
| `validate_nic` | `NicResult` | `decoded`, `format`, `dob`, `gender`, `age`, `year`, `serial`, `voting_eligible`, `dob_match`, `gender_match`, `mismatch_reasons`, `mismatch_detail` |
| `validate_postal` | `PostalResult` | `district`, `province`, `post_office`, `decoded` |

The properties read from the same `data` dict — they are **not separate
storage**, just a typed view. Both styles are stable, supported, and
interoperate freely:

```python
result = validate_phone("0712345678")
result.carrier is result.data["carrier"]    # True
result.carrier is result["carrier"]         # True
```

### Why properties return `None` on invalid results

Properties are always safe to call — they read from `data.get(...)`
under the hood, so an invalid result returns `None` rather than
raising:

```python
result = validate_phone("0001234567")  # invalid
result.is_valid    # False
result.carrier     # None — does not raise
```

This is deliberate: it lets you write linear code without
defensive `try/except` blocks around every property access. If you
*want* a hard fail on missing fields, use the dict-style form
(`result["carrier"]`).

## The `decoded` property

Every domain result has a `decoded` property that bundles the extracted
fields into a single immutable dataclass. It's a convenient way to pass
the parsed identifier around as one object:

```python
result = validate_phone("0712345678")
result.decoded
# PhoneDecoded(carrier='Mobitel', line_type='mobile', local='0712345678')

nic = validate_nic("199201409894")
nic.decoded
# NICDecoded(format='new', dob=date(1992, 1, 14), gender='male', ...)
```

The `decoded` dataclass is also `frozen=True` — safe to use as a dict
key or to share across threads.

For NIC results, every field on `decoded` is also exposed directly on
the result for ergonomics:

```python
nic.dob              # same as nic.decoded.dob
nic.gender           # same as nic.decoded.gender
nic.voting_eligible  # same as nic.decoded.voting_eligible
```

## Iteration and membership

Because results delegate to their `data` dict, the standard dict
helpers also work:

```python
result = validate_phone("0712345678")

"carrier" in result            # True — like dict membership
list(result)                   # ['decoded', 'carrier', 'line_type', 'local']
```

## Equality and hashing

`ValidationResult` does **not** override `__eq__` or `__hash__` — two
distinct results compare by identity, not by content. If you need
content equality (e.g. in tests), compare specific fields or compare
`result.data`.

## See also

- **[Error handling](errors.md)** — every error code, what triggers it,
  and how to react to it.
- **[Phone validator](../validators/phone.md)** — concrete examples
  of all four access patterns in context.
- **[NIC validator](../validators/nic.md)** — typed access on top of
  the batch / DataFrame APIs.
