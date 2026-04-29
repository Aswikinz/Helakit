# Getting Started

## Install

```bash
pip install helakit
```

Helakit supports Python 3.10 and newer and has no runtime dependencies.

## Two ways to validate

Every validator ships in two flavours: a rich one that returns a
`ValidationResult`, and a boolean shorthand.

### Rich result (recommended)

```python
from helakit import validate_nic

result = validate_nic("199012345678")
if result.is_valid:
    print(result.normalized)
    print(result.data["dob"], result.data["gender"])
else:
    for err in result.errors:
        print(err.code, err.message)
```

`ValidationResult` is truthy when valid, so plain `if validate_nic(x):`
also works.

### Boolean shorthand

```python
from helakit import is_valid_nic

is_valid_nic("199012345678")  # True
```

Use the rich form when you need parsed fields or precise error reporting,
and the shorthand when you only need a yes/no.
