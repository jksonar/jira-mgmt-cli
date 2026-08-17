"""Table/JSON/quiet rendering and dry-run/error banners."""

from __future__ import annotations

import json
from enum import Enum

import typer

from jira_cli.client.exceptions import JiraCliError
from jira_cli.models.release import Release


class OutputFormat(str, Enum):
    TABLE = "table"
    JSON = "json"


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    header_line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    typer.echo(header_line)
    typer.echo("-" * len(header_line))
    for row in rows:
        typer.echo("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))


def render_release_list(releases: list[Release], fmt: OutputFormat, quiet: bool) -> None:
    if quiet:
        for release in releases:
            typer.echo(release.id)
        return

    if fmt is OutputFormat.JSON:
        typer.echo(json.dumps([r.to_dict() for r in releases], indent=2))
        return

    rows = [
        [r.name, r.release_date or "", "yes" if r.released else "no"]
        for r in releases
    ]
    print_table(["NAME", "RELEASE DATE", "RELEASED"], rows)


def render_release(release: Release, fmt: OutputFormat, quiet: bool) -> None:
    if quiet:
        typer.echo(release.id)
        return

    if fmt is OutputFormat.JSON:
        typer.echo(json.dumps(release.to_dict(), indent=2))
        return

    typer.echo(f"Release ID: {release.id}")
    typer.echo(f"Name: {release.name}")
    if release.description:
        typer.echo(f"Description: {release.description}")
    typer.echo(f"Start Date: {release.start_date or ''}")
    typer.echo(f"Release Date: {release.release_date or ''}")
    typer.echo(f"Released: {'yes' if release.released else 'no'}")
    typer.echo(f"Archived: {'yes' if release.archived else 'no'}")


def render_deleted(version_id: str, fmt: OutputFormat, quiet: bool) -> None:
    if fmt is OutputFormat.JSON and not quiet:
        typer.echo(json.dumps({"id": version_id, "deleted": True}, indent=2))
        return
    typer.echo(f"Release {version_id} deleted." if not quiet else version_id)


def render_dry_run(operation: str, fields: dict[str, str]) -> None:
    typer.echo("DRY RUN")
    typer.echo("")
    typer.echo("No changes will be made.")
    typer.echo("")
    typer.echo("Operation:")
    typer.echo(operation)
    for label, value in fields.items():
        typer.echo("")
        typer.echo(f"{label}:")
        typer.echo(value)


def print_error(err: JiraCliError) -> None:
    typer.echo(f"ERROR: {err.message}", err=True)
    if err.details:
        typer.echo("", err=True)
        typer.echo(err.details, err=True)
