"""CalVer version calculation: format `YY.MM.DD`, where `DD` is always the last day of the month."""

from __future__ import annotations

import calendar
import re
from datetime import date

_CALVER_RE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{2})$")
_CENTURY = 2000


class InvalidCalVerError(ValueError):
    """Raised when a string does not represent a valid CalVer `YY.MM.DD` release."""


def last_day_of_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def format_calver(value: date) -> str:
    return f"{value.year % 100:02d}.{value.month:02d}.{value.day:02d}"


def parse_calver(version: str) -> date:
    """Parse and validate a `YY.MM.DD` release name, raising InvalidCalVerError if invalid.

    The day must be the last day of the given month.
    """
    match = _CALVER_RE.match(version.strip())
    if not match:
        raise InvalidCalVerError(f"'{version}' does not match the YY.MM.DD format.")

    yy, mm, dd = (int(group) for group in match.groups())
    year = _CENTURY + yy

    try:
        parsed = date(year, mm, dd)
    except ValueError as exc:
        raise InvalidCalVerError(f"'{version}' is not a valid calendar date.") from exc

    expected_day = last_day_of_month(year, mm)
    if dd != expected_day:
        raise InvalidCalVerError(
            f"'{version}' day {dd:02d} is not the last day of {year}-{mm:02d} "
            f"(expected {expected_day:02d})."
        )

    return parsed


def is_valid_calver(version: str) -> bool:
    try:
        parse_calver(version)
        return True
    except InvalidCalVerError:
        return False


def next_calver(version: str) -> str:
    """Given a valid `YY.MM.DD` release, return the next month's release (last day of that month)."""
    current = parse_calver(version)

    if current.month == 12:
        next_year, next_month = current.year + 1, 1
    else:
        next_year, next_month = current.year, current.month + 1

    next_day = last_day_of_month(next_year, next_month)
    return format_calver(date(next_year, next_month, next_day))


def latest_calver(versions: list[str]) -> str | None:
    """Return the newest valid CalVer string in `versions` (calendar order), or None if none are valid."""
    parsed = [(parse_calver(v), v) for v in versions if is_valid_calver(v)]
    if not parsed:
        return None
    return max(parsed, key=lambda pair: pair[0])[1]
