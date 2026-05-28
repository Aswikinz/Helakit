# Postal

Sri Lankan postal codes are five digits, with each code mapping to a
specific post office, district, and province.

!!! warning "Planned"
    Postal-code validation has not been implemented yet. The result
    shape and public API are settled — calling `validate_postal` today
    raises `NotImplementedError`, but the planned API below is what
    will land. Track progress on
    [GitHub](https://github.com/Aswikinz/Helakit/issues).

## Planned API

```python
from helakit import validate_postal, is_valid_postal

result = validate_postal("10100")

result.is_valid       # True
result.normalized     # "10100"
result.district       # "Colombo"
result.province       # "Western"
result.post_office    # "Colombo GPO"

is_valid_postal("10100")  # True
```

### Planned error codes

| Code | Triggered by |
| ---- | ------------ |
| `postal.invalid_length` | Not exactly 5 characters. |
| `postal.invalid_characters` | Contains non-digit characters. |
| `postal.unknown_code` | Five digits but not a code in our table. |

## `PostalResult` (planned shape)

::: helakit.postal.PostalResult
    options:
      show_root_heading: false
      show_signature: false
      members: false

## `PostalDecoded` (planned shape)

::: helakit.postal.PostalDecoded
    options:
      show_root_heading: false
      show_signature: false
      members: false
