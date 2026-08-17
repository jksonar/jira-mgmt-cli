"""Unit tests for the MAJOR.MINOR.PATCH versioning module."""

from __future__ import annotations

from datetime import date

import pytest

from jira_cli.versioning.patch import (
    InvalidPatchVersionError,
    bootstrap_patch_version,
    extract_version_prefix,
    format_patch_version,
    is_valid_patch_version,
    next_patch_version,
    parse_patch_version,
)


def test_parse_patch_version() -> None:
    assert parse_patch_version("25.10.2") == (25, 10, 2)


@pytest.mark.parametrize("value", ["25.10", "25.10.2.1", "abc", "", "25.10.-1"])
def test_parse_patch_version_rejects_invalid(value: str) -> None:
    with pytest.raises(InvalidPatchVersionError):
        parse_patch_version(value)


def test_is_valid_patch_version() -> None:
    assert is_valid_patch_version("25.10.2") is True
    assert is_valid_patch_version("25.10.2 - Release Branch") is False
    assert is_valid_patch_version("not-a-version") is False


def test_format_patch_version() -> None:
    assert format_patch_version(25, 10, 3) == "25.10.3"


def test_next_patch_version_bumps_last_segment_only() -> None:
    assert next_patch_version("25.10.2") == "25.10.3"
    assert next_patch_version("25.10.9") == "25.10.10"


def test_next_patch_version_rejects_invalid() -> None:
    with pytest.raises(InvalidPatchVersionError):
        next_patch_version("not-a-version")


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("25.10.2", "25.10.2"),
        ("25.10.3 - Release Branch", "25.10.3"),
        ("25.10.2 - in Deployment", "25.10.2"),
        ("25.10.1 - on DEV", "25.10.1"),
        ("release-test", None),
        ("", None),
    ],
)
def test_extract_version_prefix(name: str, expected: str | None) -> None:
    assert extract_version_prefix(name) == expected


def test_bootstrap_patch_version_seeds_yy_mm_1() -> None:
    assert bootstrap_patch_version(date(2026, 8, 17)) == "26.08.1"
    assert bootstrap_patch_version(date(2025, 1, 5)) == "25.01.1"
