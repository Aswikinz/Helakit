# Postal

Sri Lankan postal codes are five digits, with each code mapping to a
specific post office, district, and province.

!!! note "Coming soon"
    Postal-code validation is planned. Until then, `validate_postal`
    raises `NotImplementedError`.

## Planned API

```python
from helakit import validate_postal, is_valid_postal

result = validate_postal("10100")
result.data  # {"district": "Colombo", "province": "Western", ...}

is_valid_postal("10100")  # True
```
