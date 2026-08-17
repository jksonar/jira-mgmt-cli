"""CLI-level input validators, all raising typer.BadParameter (exit code 2) on failure."""

from __future__ import annotations

import re
from datetime import date

import typer

_PROJECT_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]+$")


def validate_project_key(value: str) -> str:
    if not _PROJECT_KEY_RE.match(value):
        raise typer.BadParameter(
            "Project key must be uppercase letters/digits, e.g. PROJ."
        )
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
