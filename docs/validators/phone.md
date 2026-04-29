# Phone

Sri Lankan phone numbers come in local (`0712345678`) and international
(`+94712345678`) forms, and the leading prefix identifies the carrier
or whether the number is mobile or fixed-line.

!!! note "Coming soon"
    Phone validation is planned. Until then, `validate_phone` raises
    `NotImplementedError`.

## Planned API

```python
from helakit import validate_phone, is_valid_phone

result = validate_phone("+94712345678")
result.normalized  # "+94712345678"
result.data        # {"type": "mobile", "carrier": "Mobitel", ...}

is_valid_phone("0712345678")  # True
```
