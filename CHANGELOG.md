# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- NIC validation, decoding, and format conversion. `validate_nic` accepts
  a single string, a list of strings, a list of dicts, a pandas DataFrame
  or a polars DataFrame, with optional cross-checking against supplied
  dates of birth and genders. `convert_nic` performs old → new format
  conversion. Pandas and polars are optional extras (`helakit[pandas]`,
  `helakit[polars]`); the library itself remains dependency-free.
- `NICDecoded`, `NICBatchResult`, `NICSummary`, `NICError`, and
  `NICFormatError` re-exported from the top-level package.

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
