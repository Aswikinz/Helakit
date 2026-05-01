# Helakit

*A toolkit for validating and working with Sri Lankan data.*

[![PyPI version](https://img.shields.io/pypi/v/helakit.svg)](https://pypi.org/project/helakit/)
[![Python versions](https://img.shields.io/pypi/pyversions/helakit.svg)](https://pypi.org/project/helakit/)
[![CI](https://github.com/Aswikinz/Helakit/actions/workflows/ci.yml/badge.svg)](https://github.com/Aswikinz/Helakit/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/codecov/c/github/Aswikinz/Helakit)](https://codecov.io/gh/Aswikinz/Helakit)
[![Docs](https://img.shields.io/badge/docs-online-blue)](https://Aswikinz.github.io/Helakit/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

Helakit is a small, dependency-free Python library for validating and
parsing Sri Lankan identifiers — NIC numbers, phone numbers, postal
codes, and more. Each identifier lives in its own self-contained
subpackage and shares a single result type, so adding a new validator
is a matter of dropping in a folder.

For usage and API reference, see the [docs](https://Aswikinz.github.io/Helakit/).
This page is a tour of *how the project is laid out* — useful if you
want to contribute, audit, or fork.

## Design principles

1. **Modular monolith.** Every validation domain (`nic`, `phone`,
   `postal`, …) is a self-contained subpackage. Adding a new domain is
   adding a new folder; no plugin system or registry to wire up.
2. **Zero runtime dependencies.** The library itself uses only the
   Python standard library. Dev and docs tools are kept in extras.
3. **Data as Python dicts.** Lookup tables (provinces, districts,
   mobile prefixes, NIC encoding rules) live as module-level `dict`
   constants in `.py` files, not JSON / Parquet / SQLite. Lookups are
   O(1) and cost nothing after import.
4. **One result shape, two entry points.** Every validator exposes
   both a rich `validate_X(value) -> ValidationResult` and a boolean
   `is_valid_X(value) -> bool`. `ValidationResult` is truthy when
   valid, so the rich form drops into `if` statements naturally.
5. **`src/` layout.** Tests run against the *installed* package, not
   the source tree, so packaging mistakes can't masquerade as passing
   tests.
6. **Strict typing end to end.** A `py.typed` marker ships with the
   wheel and CI runs `mypy --strict`. Type hints use modern syntax
   (`X | Y`, `list[X]`, `dict[K, V]`).

## Repository layout

```text
src/helakit/
├── __init__.py        # public API surface + __version__
├── py.typed           # PEP 561 marker
├── _core/             # shared primitives, no domain logic
│   ├── result.py      # ValidationResult + ValidationError dataclasses
│   ├── base.py        # Validator Protocol
│   └── exceptions.py  # HelakitError hierarchy
├── _data/             # cross-domain lookup tables (provinces, districts, …)
└── <domain>/          # one folder per identifier type
    ├── __init__.py    # re-exports validate_X / is_valid_X
    ├── validator.py   # the actual rules
    ├── exceptions.py  # domain-specific exceptions
    └── _data.py       # domain-specific lookup tables (optional)
```

Domains currently in the tree: `nic/`, `phone/`, `postal/`. The
underscore-prefixed packages (`_core/`, `_data/`) are private —
nothing outside the package should import from them.

Around the source:

```text
tests/                 # mirror of src/helakit/, one folder per domain
docs/                  # MkDocs site (Material theme, mike for versioning)
.github/workflows/     # ci.yml, docs.yml, release.yml
pyproject.toml         # hatchling build, ruff, mypy, pytest, coverage config
```

## How a domain is structured

Each domain is independent. The contract:

- `validate_X(value: str) -> ValidationResult` — full validation,
  returns parsed fields in `result.data` and structured errors in
  `result.errors`.
- `is_valid_X(value: str) -> bool` — boolean shorthand.
- A domain-specific `XError` exception class inheriting from
  `HelakitError`, for unrecoverable misuse (not validation failures —
  those go through `ValidationResult`).
- A `_data.py` for any tables only that domain cares about.

The `__init__.py` re-exports the two functions and the exception, and
the top-level `helakit/__init__.py` re-exports them again so users can
write `from helakit import validate_nic` without thinking about layout.

## Validators

| Validator | Function          | Status      |
| --------- | ----------------- | ----------- |
| NIC       | `validate_nic`    | Available   |
| Phone     | `validate_phone`  | Planned     |
| Postal    | `validate_postal` | Planned     |
| Passport  | (planned)         | Planned     |

More (driving licence numbers, BR numbers, …) will follow. Stubs for
unimplemented validators raise `NotImplementedError` so call-sites
written against the planned API don't silently no-op.

## Adding a new validator

1. Create `src/helakit/<domain>/` mirroring the layout above.
2. Add a `tests/test_<domain>/` folder with at least one test for the
   happy path and one for each error class.
3. Add a `docs/validators/<domain>.md` page.
4. Re-export the public functions from `src/helakit/__init__.py`.
5. Add a `## [Unreleased]` entry to `CHANGELOG.md`.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the dev-environment setup
and the PR checklist.

## Data contributions

A lot of helakit's value lives in its lookup tables. Adding or
correcting entries (postal codes, mobile prefixes, district names) is
the easiest way to contribute and doesn't require deep Python — each
table is a plain `dict` in `src/helakit/_data/` or
`src/helakit/<domain>/_data.py`. Cite a source in the PR description
so we can verify it.

## Documentation

Docs are versioned with [mike](https://github.com/jimporter/mike) and
published in three flavours:

- `/dev/` — built from every push to `main`. Tracks in-progress work.
- `/<MAJOR>.<MINOR>/` — built from each release tag. Frozen.
- `/latest/` — alias for the most recent release.

The bare site URL ([Aswikinz.github.io/Helakit](https://Aswikinz.github.io/Helakit/))
redirects to `/latest/` once a release exists, and to `/dev/` until then.

Links: [docs](https://Aswikinz.github.io/Helakit/) ·
[dev](https://Aswikinz.github.io/Helakit/dev/) ·
[changelog](CHANGELOG.md) ·
[contributing](CONTRIBUTING.md).

## Install

```bash
pip install helakit
```

Requires Python 3.10+.

## Status

Helakit is alpha software. The public API may change before 1.0; pin
versions accordingly.

## License

Apache License 2.0 — see [LICENSE](LICENSE).
