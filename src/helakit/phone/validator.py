"""Phone-number validation for Sri Lankan numbers.

Supports both local (``"0712345678"``) and international (``"+94712345678"``)
formats.  The validator normalises input, checks length and prefix, and
returns a :class:`~helakit._core.result.ValidationResult` with carrier and
line-type metadata on success.
"""

from __future__ import annotations

import re

from helakit._core.exceptions import InvalidInputError
from helakit._core.result import ValidationError, ValidationResult
from helakit.phone._data import (
    ALL_PREFIXES,
    COUNTRY_CODE,
    INTL_PREFIX,
    INTL_LENGTH,
    LOCAL_LENGTH,
)

_DIGIT_RE = re.compile(r"^\+?\d+$")


def validate_phone(value: str) -> ValidationResult:
    """Validate a Sri Lankan phone number.

    Args:
        value: The phone number in local (``"0712345678"``) or international
            (``"+94712345678"``) form.  Spaces and hyphens are stripped
            before validation.

    Returns:
        A :class:`~helakit._core.result.ValidationResult`.  When valid,
        ``normalized`` holds the canonical ``+94XXXXXXXXX`` form and
        ``data`` contains:

        - ``"carrier"`` – the network operator name (e.g. ``"Dialog"``).
        - ``"line_type"`` – ``"mobile"`` or ``"fixed"``.
        - ``"local"`` – the local ``0XXXXXXXXX`` representation.

    Raises:
        InvalidInputError: If ``value`` is not a string.
    """
    if not isinstance(value, str):
        raise InvalidInputError(
            f"validate_phone requires a string; got {type(value).__name__}."
        )

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
        return ValidationResult(is_valid=False, value=value, errors=errors)

    local, err = _to_local(cleaned)
    if err:
        errors.append(err)
        return ValidationResult(is_valid=False, value=value, errors=errors)

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
        return ValidationResult(is_valid=False, value=value, errors=errors)

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
        return ValidationResult(is_valid=False, value=value, errors=errors)

    normalized = INTL_PREFIX + local[1:]
    return ValidationResult(
        is_valid=True,
        value=value,
        normalized=normalized,
        data={
            "carrier": info.carrier,
            "line_type": info.line_type,
            "local": local,
        },
    )


def is_valid_phone(value: str) -> bool:
    """Return ``True`` if ``value`` is a valid Sri Lankan phone number.

    Args:
        value: The phone number to check (local or international form).

    Returns:
        ``True`` when valid, ``False`` otherwise.

    Raises:
        InvalidInputError: If ``value`` is not a string.
    """
    return validate_phone(value).is_valid


def _clean(value: str) -> str:
    return re.sub(r"[\s\-()]", "", value)


def _to_local(cleaned: str) -> tuple[str, ValidationError | None]:
    if cleaned.startswith(INTL_PREFIX):
        digits = cleaned[len(INTL_PREFIX):]
        if not digits.startswith("0"):
            digits = "0" + digits
        return digits, None

    if cleaned.startswith(COUNTRY_CODE) and len(cleaned) == INTL_LENGTH:
        return "0" + cleaned[len(COUNTRY_CODE):], None

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
