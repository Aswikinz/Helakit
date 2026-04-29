# Helakit

*A toolkit for validating and working with Sri Lankan data.*

[![PyPI version](https://img.shields.io/pypi/v/helakit.svg)](https://pypi.org/project/helakit/)
[![Python versions](https://img.shields.io/pypi/pyversions/helakit.svg)](https://pypi.org/project/helakit/)
[![CI](https://github.com/Aswikinz/Helakit/actions/workflows/ci.yml/badge.svg)](https://github.com/Aswikinz/Helakit/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/codecov/c/github/Aswikinz/Helakit)](https://codecov.io/gh/Aswikinz/Helakit)
[![Docs](https://img.shields.io/badge/docs-latest-blue)](https://Aswikinz.github.io/Helakit/latest/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Helakit is a small, dependency-free Python library for validating and
parsing Sri Lankan identifiers — NIC numbers, phone numbers, postal
codes, and more. Built around a single `ValidationResult` shape so every
validator looks and feels the same.

## Install

```bash
pip install helakit
```

Requires Python 3.10+. No runtime dependencies.

## Quick example

```python
from helakit import validate_nic

result = validate_nic("199012345678")
if result.is_valid:
    print(result.data["dob"], result.data["gender"])
else:
    for err in result.errors:
        print(err.message)
```

If you only need a yes/no, every validator ships a boolean shorthand:

```python
from helakit import is_valid_nic
is_valid_nic("199012345678")  # True
```

## Validators

| Validator | Function                | Status      |
| --------- | ----------------------- | ----------- |
| NIC       | `validate_nic`          | In progress |
| Phone     | `validate_phone`        | Planned     |
| Postal    | `validate_postal`       | Planned     |
| Passport  | `validate_passport`     | Planned     |
| Vehicle   | `validate_vehicle`      | Planned     |

More validators (driving licence numbers, BR numbers, …) will follow.

## Documentation

- Latest release: <https://Aswikinz.github.io/Helakit/latest/>
- Development build (tracks `main`): <https://Aswikinz.github.io/Helakit/dev/>
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Status

Helakit is alpha software. The public API may change before 1.0; pin
versions accordingly.

## License

MIT — see [LICENSE](LICENSE).
