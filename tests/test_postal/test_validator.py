"""Placeholder tests for the postal-code validator stubs."""

from __future__ import annotations

import pytest

from helakit import is_valid_postal, validate_postal


def test_validate_postal_is_stubbed() -> None:
    with pytest.raises(NotImplementedError):
        validate_postal("10100")


def test_is_valid_postal_is_stubbed() -> None:
    with pytest.raises(NotImplementedError):
        is_valid_postal("10100")
