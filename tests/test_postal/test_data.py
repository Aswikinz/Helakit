"""Integrity tests for the postal-code lookup table.

These guard the data itself rather than the validator: every row has to point
at a district that exists, and every district has to sit in a real province,
or ``validate_postal`` would raise a ``KeyError`` on a perfectly good code.
"""

from __future__ import annotations

import re

from helakit._data.districts import DISTRICT_PROVINCE, DISTRICTS
from helakit._data.provinces import PROVINCES
from helakit.postal._data import POSTAL_CODE_LENGTH, POSTAL_CODES

_CODE_RE = re.compile(r"^[0-9]{5}$")


def test_table_is_populated() -> None:
    assert len(POSTAL_CODES) > 2000


def test_every_key_is_a_five_digit_string() -> None:
    bad = [code for code in POSTAL_CODES if not _CODE_RE.match(code)]
    assert bad == []
    assert POSTAL_CODE_LENGTH == 5


def test_every_entry_has_a_known_district() -> None:
    unknown = {e.district for e in POSTAL_CODES.values()} - set(DISTRICTS)
    assert unknown == set()


def test_every_district_resolves_to_a_province() -> None:
    for entry in POSTAL_CODES.values():
        assert entry.district in DISTRICT_PROVINCE
        assert DISTRICT_PROVINCE[entry.district] in PROVINCES


def test_all_twenty_five_districts_are_represented() -> None:
    assert {e.district for e in POSTAL_CODES.values()} == set(DISTRICTS)


def test_post_office_names_are_non_empty() -> None:
    assert [c for c, e in POSTAL_CODES.items() if not e.post_office.strip()] == []


def test_sub_post_flag_is_boolean() -> None:
    assert {type(e.sub_post) for e in POSTAL_CODES.values()} == {bool}


def test_table_contains_both_main_and_sub_post_offices() -> None:
    kinds = {e.sub_post for e in POSTAL_CODES.values()}
    assert kinds == {True, False}


def test_known_landmark_codes() -> None:
    assert POSTAL_CODES["00100"].post_office == "Colombo 01"
    assert POSTAL_CODES["10250"].post_office == "Nugegoda"
    assert POSTAL_CODES["20000"].district == "KAN"
    assert POSTAL_CODES["80000"].post_office == "Galle"
    assert POSTAL_CODES["82600"].post_office == "Tissamaharama"


def test_counts_match_the_numbers_quoted_in_the_docs() -> None:
    """Keeps the prose honest.

    ``README.md``, ``docs/index.md`` and ``docs/validators/postal.md`` all
    quote these totals, and the postal docs carry a per-province table. If
    you add or correct entries this test will fail — update those numbers
    in the same pull request, then update the numbers here.
    """
    assert len(POSTAL_CODES) == 2121
    assert sum(1 for e in POSTAL_CODES.values() if not e.sub_post) == 592
    assert sum(1 for e in POSTAL_CODES.values() if e.sub_post) == 1529


def test_documented_data_correction_is_applied() -> None:
    """``60043`` is listed under Kandy in the directory's English column but
    Kurunegala in its Sinhala and Tamil columns, and the ``60xxx`` block is
    Kurunegala. Recorded as Kurunegala; see the ``_data`` module docstring."""
    assert POSTAL_CODES["60043"].district == "KUR"
