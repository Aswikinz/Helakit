# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- pandas-style API on `NICBatchResult` so batch results feel like the
  containers DataFrame users already know:
  - `to_pandas()` / `to_polars()` — return the batch as a DataFrame for
    *any* input shape (list, list-of-dicts, Series, DataFrame), not just
    DataFrame input.
  - `to_dicts()` — list of flat record dicts, zero optional dependencies.
  - `describe()` — the `NICSummary` roll-up, mirroring `DataFrame.describe()`.
  - `is_valid` — row-aligned boolean mask that drops into `df[batch.is_valid]`.
  - `valid` / `invalid` — filtered lists of per-row results.
  - `head(n)` and slice indexing (`batch[:3]`), mirroring pandas.
  - a concise `repr` showing the summary counts.
- `NicResult.to_dict()` flattens a single result into the same record
  shape as one `to_pandas()` row; `NICSummary.to_dict()` returns the
  counts as a plain dict.
- `validate_nic` now accepts a pandas or polars **Series** directly
  (`validate_nic(df["nic"])`), treated like a list of strings. Previously
  Series input crashed with an `AttributeError` (pandas) or a misleading
  `nic_col is required` error (polars).

### Changed

- `convert_nic` now validates new-format (12-digit) input instead of
  passing it through unchecked. A 12-digit string that encodes an
  impossible birth date (day code out of range, phantom Feb 29 in a
  non-leap year) now raises `NICFormatError` — or coerces to `None`
  under `errors="coerce"` — instead of being silently returned as-is.
- `NICDecoded.age` is now computed on access instead of being baked into the
  immutable result at validation time, so it no longer goes stale. Age is no
  longer a constructor field on `NICDecoded`. New `NICDecoded.age_at(today)`
  (and `NicResult.age_at(today)`) compute completed years against an explicit
  reference date for deterministic, testable results; the `age` property
  remains as a convenience measured against the current date.

### Fixed

- `validate_nic` no longer raises an unhandled `ValueError` on a new-format
  NIC whose four-digit year decodes to `0000` (e.g. `"000020000018"`). The
  year is outside the range `datetime.date` can represent, so it is now
  reported as a `nic.invalid_date` validation error instead. Previously this
  also aborted an entire batch when one such row was present.

## [0.2.0] - 2026-05-05

### Added

- `errors` keyword on `convert_nic` and `validate_nic`, mirroring
  `pandas.to_numeric(errors=...)` semantics. `convert_nic` accepts
  `"raise"` (default), `"coerce"` (replace bad values with `None`), or
  `"ignore"` (pass the original input through unchanged). `validate_nic`
  accepts `"raise"` (default) or `"coerce"`; the latter turns previously
  fatal `dob` / `gender` cross-check failures into per-row
  `nic.bad_dob_input` / `nic.bad_gender_input` validation errors so a
  single malformed row no longer aborts the whole batch.
- `error_col` keyword on `convert_nic` for DataFrame input — adds a
  per-row error-message column alongside `nic_converted`. Implies
  `errors="coerce"` when `errors` is left at the default.

## [0.1.1] - 2026-05-01

### Added

- NIC validation, decoding, and format conversion. `validate_nic` accepts
  a single string, a list of strings, a list of dicts, a pandas DataFrame
  or a polars DataFrame, with optional cross-checking against supplied
  dates of birth and genders. `convert_nic` performs old → new format
  conversion. Pandas and polars are optional extras (`helakit[pandas]`,
  `helakit[polars]`); the library itself remains dependency-free.
- `NICDecoded`, `NICBatchResult`, `NICSummary`, `NICError`, and
  `NICFormatError` re-exported from the top-level package.
- Helakit brand identity in the docs site: SVG logo and tick favicon,
  brand-palette stylesheet (teal / forest / cream / teal-soft) wired
  into Material's CSS variables for both schemes, slab-serif headings.
- Homepage hero with brand artwork, featured-validator block for NIC,
  and a roadmap pill row for upcoming validators.

### Changed

- Homepage navigation buttons now render Material icons inline
  (`pymdownx.emoji` enabled).
- Material `.md-button` styling pinned to teal-soft borders / labels so
  secondary buttons stay visible in both light and dark modes.
- Docs default to light mode, with dark mode kicked in by OS preference
  and a manual toggle in the header.
- Light-mode header now uses forest (`#091717`) as the primary colour
  so the teal helakit-icon stands out against it.
- Validator pages get a previous / next pair at the bottom
  (`navigation.footer`), and the page TOC moves back to the right column
  (`toc.integrate` removed) for tidier sidebar alignment.

### Removed

- Vehicle registration validator from the planned roadmap.
- Brand-colour swatch and "What's inside" sections from the homepage.

### Notes

- The Sri Lankan NIC modulo-11 check digit algorithm is not publicly
  documented; helakit extracts the digit but does not yet verify it.
- Day 60 is reserved for Feb 29 in every year (leap or not); in non-leap
  years that code is rejected as a phantom date and days 61-366 shift
  down by one to land on the actual calendar.

## [0.1.0] - 2026-04-29

### Added

- Initial scaffolding: package layout, validator stubs (NIC, phone, postal),
  `ValidationResult` core, docs site, CI / docs / release workflows, and
  development tooling (ruff, mypy, pytest, pre-commit).
