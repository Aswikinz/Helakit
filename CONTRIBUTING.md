# Contributing to Helakit

Thanks for your interest in helakit! This page walks through setting up a
local dev environment, running the checks, and submitting a PR.

## Dev environment

Helakit uses [uv](https://docs.astral.sh/uv/) for project and dependency
management. Once `uv` is installed:

```bash
uv sync --all-extras       # create a venv and install dev + docs extras
uv run pre-commit install  # wire up the git pre-commit hook
```

Everything below assumes you're running through `uv run`, which uses the
project's pinned environment.

## Running the checks

```bash
uv run pytest                    # tests + coverage
uv run ruff check .              # lint
uv run ruff format --check .     # formatting
uv run mypy src                  # type check (strict)
uv run pre-commit run --all-files
```

To preview the docs locally:

```bash
uv run mkdocs serve
```

## Pull request checklist

Before opening a PR, please make sure:

- [ ] Tests are added or updated for any behaviour change.
- [ ] Docs are updated for anything user-visible.
- [ ] An entry has been added to `CHANGELOG.md` under `[Unreleased]`.
- [ ] `ruff check`, `ruff format --check`, `mypy src`, and `pytest` all pass.

## Documentation

Docs are published in three flavours, courtesy of
[mike](https://github.com/jimporter/mike):

- `<site>/dev/` — built from every push to `main`. Always reflects
  in-progress work and may be ahead of the latest release.
- `<site>/<MAJOR>.<MINOR>/` — built from each release tag (`v0.1.0`,
  `v0.2.0`, …). Versioned, frozen.
- `<site>/latest/` — alias that always points at the most recent release.
  The bare site URL redirects here.

Visitors hitting the bare site URL land on `/latest/` by default, so the
homepage always shows the newest released version.

## Data contributions are welcome

A lot of helakit's value comes from accurate lookup tables — postal
codes, mobile prefixes, district names, and so on. Adding entries (or
correcting existing ones) is one of the easiest ways to contribute and
doesn't require deep Python knowledge: each table is a plain dict in
`src/helakit/_data/`. Please cite a source in the PR description so we
can verify the data.
