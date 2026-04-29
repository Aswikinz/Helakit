# Helakit

*A toolkit for validating and working with Sri Lankan data.*

Helakit is a small, dependency-free Python library for validating
Sri Lankan identifiers — NIC numbers, phone numbers, postal codes,
and more.

```python
from helakit import validate_nic

result = validate_nic("199012345678")
if result.is_valid:
    print(result.data["dob"], result.data["gender"])
```

See [Getting Started](getting-started.md) to install and try it,
or jump to a specific validator:

- [NIC](validators/nic.md)
- [Phone](validators/phone.md)
- [Postal](validators/postal.md)

!!! warning "Alpha software"
    Helakit is pre-1.0. The API may change before the first stable release.
