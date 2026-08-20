"""CLI-level input validators, all raising typer.BadParameter (exit code 2) on failure."""

from __future__ import annotations

import re
from datetime import date

import typer

_PROJECT_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]+$")
_ISSUE_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]+-\d+$")
_SYSTEM_KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]+$")


def validate_project_key(value: str) -> str:
    if not _PROJECT_KEY_RE.match(value):
        raise typer.BadParameter(
            "Project key must be uppercase letters/digits, e.g. PROJ."
        )
    return value


def validate_system_key(value: str | None) -> str | None:
    """Normalize the owning system's short code (e.g. "wdd", "CRM") to uppercase.

    This is the prefix that scopes release names to one system (WEB/SFCC,
    CRM, APP, ...) so pipelines sharing a Jira project never touch each
    other's versions.
    """
    if value is None:
        return None
    if not _SYSTEM_KEY_RE.match(value):
        raise typer.BadParameter(
            "System key must be letters/digits, e.g. WDD or CRM."
        )
    return value.upper()


def validate_issue_key(value: str) -> str:
    if not _ISSUE_KEY_RE.match(value):
        raise typer.BadParameter(
            "Issue key must look like PROJ-123."
        )
    return value


def validate_jql(value: str) -> str:
    if not value.strip():
        raise typer.BadParameter("JQL query cannot be empty.")
    return value


def validate_release_name(value: str) -> str:
    if not value.strip():
        raise typer.BadParameter("Release name cannot be empty.")
    return value


def validate_date_string(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise typer.BadParameter("Date must be in YYYY-MM-DD format.") from exc
    return value
