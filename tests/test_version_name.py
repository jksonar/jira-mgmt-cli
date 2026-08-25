"""Unit tests for clean_version_name, ported from devops-jrmt's cleanVersionName."""

from __future__ import annotations

import pytest

from jira_cli.utils.version_name import clean_version_name


def test_strips_bare_token() -> None:
    assert clean_version_name("25.10.1 - on DEV", "DEV") == "25.10.1"


def test_no_token_just_trims() -> None:
    assert clean_version_name("  25.10.2 - Release Branch  ") == "25.10.2"


def test_truncates_from_first_dash_when_no_slash() -> None:
    assert clean_version_name("25.10.2 - in Deployment", "in Deployment") == "25.10.2"


def test_preserves_dashes_when_name_has_slash_before_stripping() -> None:
    # A slash-delimited name keeps its dashes even after the token is stripped,
    # since the "truncate from first dash" rule only applies to slash-free names.
    assert clean_version_name("release/25.10-DEV/build", "DEV") == "release/25.10-build"


def test_strips_token_with_leading_slash() -> None:
    assert clean_version_name("release/DEV/25.10", "DEV") == "release/25.10"


def test_strips_token_with_trailing_slash() -> None:
    assert clean_version_name("release/25.10/DEV", "DEV") == "release/25.10"


def test_collapses_duplicate_slashes() -> None:
    assert clean_version_name("a//b") == "a/b"


def test_strips_trailing_slash() -> None:
    assert clean_version_name("release/25.10/", None) == "release/25.10"


def test_empty_token_raises() -> None:
    with pytest.raises(ValueError):
        clean_version_name("25.10.1", "")


def test_non_string_name_raises() -> None:
    with pytest.raises(TypeError):
        clean_version_name(None, "DEV")  # type: ignore[arg-type]


def test_system_key_prefix_is_preserved_across_strip() -> None:
    assert (
        clean_version_name("WEB - 25.10.2 - on DEV", "DEV", system_key="WEB")
        == "WEB - 25.10.2"
    )


def test_system_key_prefix_preserved_with_no_token() -> None:
    assert (
        clean_version_name("CRM - 25.10.2 - Release Branch", system_key="CRM")
        == "CRM - 25.10.2"
    )


def test_mismatched_system_key_prefix_is_not_stripped() -> None:
    # Name doesn't carry the given system_key's prefix, so it's cleaned as-is
    # (and still hits the legacy first-dash truncation).
    assert clean_version_name("CRM - 25.10.2 - on DEV", "DEV", system_key="WEB") == "CRM"
