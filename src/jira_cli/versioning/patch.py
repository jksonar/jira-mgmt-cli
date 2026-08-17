"""Patch version calculation: format `MAJOR.MINOR.PATCH`, where only the patch
segment is a simple incrementing counter (no calendar meaning, unlike CalVer)."""

from __future__ import annotations

import re
from datetime import date

_PATCH_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
_PATCH_PREFIX_RE = re.compile(r"^(\d+\.\d+\.\d+)(?:\s|$)")


class InvalidPatchVersionError(ValueError):
    """Raised when a string does not represent a valid MAJOR.MINOR.PATCH version."""


def parse_patch_version(version: str) -> tuple[int, int, int]:
    match = _PATCH_RE.match(version.strip())
    if not match:
        raise InvalidPatchVersionError(
            f"'{version}' does not match the MAJOR.MINOR.PATCH format."
        )
    major, minor, patch = (int(group) for group in match.groups())
    return major, minor, patch


def is_valid_patch_version(version: str) -> bool:
    try:
        parse_patch_version(version)
        return True
    except InvalidPatchVersionError:
        return False


def format_patch_version(major: int, minor: int, patch: int) -> str:
    return f"{major}.{minor}.{patch}"


def next_patch_version(version: str) -> str:
    """Bump only the patch segment; major.minor is carried over unchanged."""
    major, minor, patch = parse_patch_version(version)
    return format_patch_version(major, minor, patch + 1)


def extract_version_prefix(name: str) -> str | None:
    """Return the leading MAJOR.MINOR.PATCH token in `name`, or None if absent.

    Used to identify a release regardless of what suffix/label currently
    follows the version, e.g. "25.10.2 - in Deployment" -> "25.10.2".
    """
    match = _PATCH_PREFIX_RE.match(name.strip())
    return match.group(1) if match else None


def bootstrap_patch_version(today: date) -> str:
    """No prior release exists yet: seed `YY.MM.1` from today's date."""
    return f"{today.year % 100:02d}.{today.month:02d}.1"
