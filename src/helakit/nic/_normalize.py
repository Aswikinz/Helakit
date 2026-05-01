"""String canonicalisation for NIC values."""

from __future__ import annotations

from helakit.nic._data import OLD_FORMAT_SUFFIXES


def normalize(value: str) -> str:
    """Trim whitespace and uppercase the input.

    Args:
        value: Raw NIC string.

    Returns:
        The same string with leading/trailing whitespace removed and any
        ASCII letters uppercased.
    """
    return value.strip().upper()


def normalize_for_dedup(value: str) -> str:
    """Canonical form for duplicate detection.

    Strips the trailing ``V``/``X`` suffix on old-format NICs so that a card
    reissued with a different voting status still compares equal to the
    original.
    """
    cleaned = normalize(value)
    if cleaned and cleaned[-1] in OLD_FORMAT_SUFFIXES:
        return cleaned[:-1]
    return cleaned
