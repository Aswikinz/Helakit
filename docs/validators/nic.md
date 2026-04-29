# NIC

Sri Lanka issues a National Identity Card number that encodes the
holder's date of birth, gender, and (in the old format) voting eligibility.

!!! note "Coming soon"
    NIC validation is the next thing to land. Until then, calling
    `validate_nic` raises `NotImplementedError`.

## Planned API

```python
from helakit import validate_nic, is_valid_nic

result = validate_nic("199012345678")
result.data       # {"dob": date(1990, 5, 4), "gender": "male", ...}
result.normalized # "199012345678"

is_valid_nic("199012345678")  # True
```

Both old (`901234567V`) and new (`199012345678`) formats will be supported.
