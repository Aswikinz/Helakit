"""NIC validation entry points.

Both :func:`validate_nic` and :func:`is_valid_nic` are stubs for now and
will be implemented in a follow-up release.
"""

from __future__ import annotations

from helakit._core.result import ValidationResult


def validate_nic(value: str) -> ValidationResult:
    """Validate a Sri Lankan NIC number and return a structured result.

    Args:
        value: The NIC number as a string. Both old (e.g. ``"901234567V"``)
            and new (e.g. ``"199012345678"``) formats will be accepted.

    Returns:
        A :class:`ValidationResult` with parsed fields (date of birth,
        gender, voting eligibility, …) populated when valid.

    Raises:
        NotImplementedError: NIC validation has not been implemented yet.
    """
    raise NotImplementedError("Coming in a future release")


def is_valid_nic(value: str) -> bool:
    """Return ``True`` if ``value`` is a valid Sri Lankan NIC number.

    Args:
        value: The NIC number as a string.

    Raises:
        NotImplementedError: NIC validation has not been implemented yet.
    """
    raise NotImplementedError("Coming in a future release")
