"""Phone-number validation for Sri Lankan numbers.

Supports both local (``"0712345678"``) and international (``"+94712345678"``)
formats. The validator normalises input, checks length and prefix, and
returns a :class:`~helakit.phone.PhoneResult` with carrier and line-type
metadata on success.
"""

from __future__ import annotations

import re

from helakit._core.exceptions import InvalidInputError
from helakit._core.result import ValidationError
from helakit.phone._data import (
    ALL_PREFIXES,
    COUNTRY_CODE,
    INTL_LENGTH,
    INTL_PREFIX,
    LOCAL_LENGTH,
)
from helakit.phone._types import PhoneDecoded, PhoneResult

_DIGIT_RE = re.compile(r"^\+?[0-9]+$")


def validate_phone(value: str) -> PhoneResult:
    """Validate a Sri Lankan phone number.

    The validator accepts numbers in three input forms — local
    (``"0712345678"``), international with leading ``+``
    (``"+94712345678"``), and international without the ``+``
    (``"94712345678"``) — and tolerates spaces, hyphens, and parentheses
    inside the number (they are stripped before validation).

    Args:
        value: The phone number as a string. Must contain ASCII digits
            only (optionally prefixed with ``+``); Unicode digits and
            other characters cause a ``phone.invalid_characters`` error.

    Returns:
        A :class:`PhoneResult`. When valid, ``normalized`` holds the
        canonical ``"+94XXXXXXXXX"`` form and the following typed
        properties are populated:

        - ``carrier`` — network operator name (e.g. ``"Mobitel"``).
        - ``line_type`` — ``"mobile"`` or ``"fixed"``.
        - ``local`` — the ``"0XXXXXXXXX"`` local representation.
        - ``decoded`` — a :class:`PhoneDecoded` bundling the above.

        On invalid input, ``is_valid`` is ``False``, ``normalized`` is
        ``None``, and ``errors`` contains one or more
        :class:`~helakit._core.result.ValidationError`\\ s with codes from
        the table below.

    Raises:
        InvalidInputError: If ``value`` is not a string. This is a
            programmer error (not a validation failure) — passing
            ``None`` or an ``int`` is treated as misuse, not as bad data.

    Error codes:
        - ``phone.invalid_characters`` — input contains characters other
          than ASCII digits and an optional leading ``+``.
        - ``phone.missing_prefix`` — input has no recognisable leading
          ``0``, ``+94``, or ``94``.
        - ``phone.invalid_length`` — input has the right shape but the
          wrong number of digits (must be 10 in local form).
        - ``phone.unknown_prefix`` — the three-digit local prefix is not
          a Sri Lankan mobile or fixed-line prefix.

    Example:
        Basic validation::

            >>> result = validate_phone("0712345678")
            >>> result.is_valid
            True
            >>> result.normalized
            '+94712345678'
            >>> result.carrier
            'Mobitel'
            >>> result.line_type
            'mobile'

        International form::

            >>> validate_phone("+94772345678").carrier
            'Dialog'

        Formatting tolerance::

            >>> validate_phone("071 234 5678").is_valid
            True
            >>> validate_phone("(071) 234-5678").is_valid
            True

        Handling invalid input::

            >>> result = validate_phone("0001234567")
            >>> result.is_valid
            False
            >>> result.errors[0].code
            'phone.unknown_prefix'
    """
    if not isinstance(value, str):
        raise InvalidInputError(f"validate_phone requires a string; got {type(value).__name__}.")

    cleaned = _clean(value)
    errors: list[ValidationError] = []

    if not cleaned or not _DIGIT_RE.match(cleaned):
        errors.append(
            ValidationError(
                code="phone.invalid_characters",
                message="Phone number must contain digits only (optionally prefixed with '+').",
                field="value",
            )
        )
        return PhoneResult(is_valid=False, value=value, errors=errors)

    local, err = _to_local(cleaned)
    if err:
        errors.append(err)
        return PhoneResult(is_valid=False, value=value, errors=errors)

    if len(local) != LOCAL_LENGTH:
        errors.append(
            ValidationError(
                code="phone.invalid_length",
                message=(
                    f"Sri Lankan phone numbers must be {LOCAL_LENGTH} digits "
                    f"in local form; got {len(local)}."
                ),
                field="value",
            )
        )
        return PhoneResult(is_valid=False, value=value, errors=errors)

    prefix = local[:3]
    info = ALL_PREFIXES.get(prefix)
    if info is None:
        errors.append(
            ValidationError(
                code="phone.unknown_prefix",
                message=f"Prefix '{prefix}' is not a recognised Sri Lankan network prefix.",
                field="value",
            )
        )
        return PhoneResult(is_valid=False, value=value, errors=errors)

    normalized = INTL_PREFIX + local[1:]
    decoded = PhoneDecoded(carrier=info.carrier, line_type=info.line_type, local=local)
    return PhoneResult(
        is_valid=True,
        value=value,
        normalized=normalized,
        data={
            "decoded": decoded,
            "carrier": decoded.carrier,
            "line_type": decoded.line_type,
            "local": decoded.local,
        },
    )


def is_valid_phone(value: str) -> bool:
    """Return ``True`` if ``value`` is a valid Sri Lankan phone number.

    Boolean shorthand for :func:`validate_phone`. Use this when you only
    need a yes/no answer; use :func:`validate_phone` when you also need
    carrier metadata or the normalized form.

    Args:
        value: The phone number to check, in local or international form.

    Returns:
        ``True`` when the number is valid, ``False`` otherwise.

    Raises:
        InvalidInputError: If ``value`` is not a string.

    Example:
        >>> is_valid_phone("0712345678")
        True
        >>> is_valid_phone("0001234567")
        False
    """
    return validate_phone(value).is_valid


def _clean(value: str) -> str:
    return re.sub(r"[\s\-()]", "", value)


def _to_local(cleaned: str) -> tuple[str, ValidationError | None]:
    if cleaned.startswith(INTL_PREFIX):
        digits = cleaned[len(INTL_PREFIX) :]
        if not digits.startswith("0"):
            digits = "0" + digits
        return digits, None

    if cleaned.startswith(COUNTRY_CODE) and len(cleaned) == INTL_LENGTH:
        return "0" + cleaned[len(COUNTRY_CODE) :], None

    if cleaned.startswith("0"):
        return cleaned, None

    return "", ValidationError(
        code="phone.missing_prefix",
        message=(
            "Phone number must start with '0' (local), '+94' or '94' (international). "
            f"Got: '{cleaned[:6]}...'"
        ),
        field="value",
    )
