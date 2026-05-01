# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
