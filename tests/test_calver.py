"""Unit tests for CalVer (YY.MM.DD) parsing, validation, and next-release calculation."""

from __future__ import annotations

import pytest

from jira_cli.versioning.calver import (
    InvalidCalVerError,
    is_valid_calver,
    last_day_of_month,
    latest_calver,
    next_calver,
    parse_calver,
)


@pytest.mark.parametrize(
    ("current", "expected"),
    [
        ("26.07.31", "26.08.31"),
        ("26.08.31", "26.09.30"),
        ("26.09.30", "26.10.31"),
        ("26.11.30", "26.12.31"),
        ("26.12.31", "27.01.31"),
        ("28.01.31", "28.02.29"),  # leap year
        ("27.01.31", "27.02.28"),  # non-leap year
    ],
)
def test_next_calver(current: str, expected: str) -> None:
    assert next_calver(current) == expected


@pytest.mark.parametrize(
    "version",
    ["26.08.31", "26.09.30", "27.01.31", "28.02.29"],
)
def test_is_valid_calver_accepts_valid(version: str) -> None:
    assert is_valid_calver(version) is True


@pytest.mark.parametrize(
    "version",
    [
        "1.2.3",
        "26.8.31",
        "2026.08.31",
        "26-08-31",
        "26.08.15",  # not the last day of August
        "26.13.31",  # invalid month
        "not-a-version",
        "",
    ],
)
def test_is_valid_calver_rejects_invalid(version: str) -> None:
    assert is_valid_calver(version) is False


def test_parse_calver_raises_on_invalid_format() -> None:
    with pytest.raises(InvalidCalVerError):
        parse_calver("v1.2.0")


def test_parse_calver_raises_when_day_is_not_last_of_month() -> None:
    with pytest.raises(InvalidCalVerError):
        parse_calver("26.08.15")


def test_last_day_of_month() -> None:
    assert last_day_of_month(2026, 2) == 28
    assert last_day_of_month(2028, 2) == 29
    assert last_day_of_month(2026, 4) == 30
    assert last_day_of_month(2026, 12) == 31


def test_latest_calver_orders_by_calendar_date_not_string() -> None:
    assert latest_calver(["26.12.31", "27.01.31"]) == "27.01.31"
    assert latest_calver(["26.06.30", "26.07.31"]) == "26.07.31"


def test_latest_calver_ignores_invalid_versions() -> None:
    versions = ["1.0.0", "26.07.31", "release-test", "26.08.31"]
    assert latest_calver(versions) == "26.08.31"


def test_latest_calver_returns_none_when_no_valid_versions() -> None:
    assert latest_calver(["1.0.0", "release-test"]) is None
