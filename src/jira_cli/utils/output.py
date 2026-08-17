"""Table/JSON/quiet rendering and dry-run/error banners."""

from __future__ import annotations

import json
from enum import Enum

import typer

from jira_cli.client.exceptions import JiraCliError
from jira_cli.models.issue import Issue
from jira_cli.models.project import Project
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
        [r.id, r.name, r.release_date or "", "yes" if r.released else "no"]
        for r in releases
    ]
    print_table(["ID", "NAME", "RELEASE DATE", "RELEASED"], rows)


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


def render_project_list(projects: list[Project], fmt: OutputFormat, quiet: bool) -> None:
    if quiet:
        for project in projects:
            typer.echo(project.key)
        return

    if fmt is OutputFormat.JSON:
        typer.echo(json.dumps([p.to_dict() for p in projects], indent=2))
        return

    rows = [[p.id or "", p.key, p.name, p.project_type or ""] for p in projects]
    print_table(["ID", "KEY", "NAME", "TYPE"], rows)


def render_project(project: Project, fmt: OutputFormat, quiet: bool) -> None:
    if quiet:
        typer.echo(project.key)
        return

    if fmt is OutputFormat.JSON:
        typer.echo(json.dumps(project.to_dict(), indent=2))
        return

    typer.echo(f"Project Key: {project.key}")
    typer.echo(f"Name: {project.name}")
    if project.lead:
        typer.echo(f"Lead: {project.lead}")
    typer.echo(f"Type: {project.project_type or ''}")


def render_issue_list(issues: list[Issue], fmt: OutputFormat, quiet: bool) -> None:
    if quiet:
        for issue in issues:
            typer.echo(issue.key)
        return

    if fmt is OutputFormat.JSON:
        typer.echo(json.dumps([i.to_dict() for i in issues], indent=2))
        return

    rows = [
        [i.key, i.summary, i.status or "", i.assignee or ""] for i in issues
    ]
    print_table(["KEY", "SUMMARY", "STATUS", "ASSIGNEE"], rows)


def render_issue(issue: Issue, fmt: OutputFormat, quiet: bool) -> None:
    if quiet:
        typer.echo(issue.key)
        return

    if fmt is OutputFormat.JSON:
        typer.echo(json.dumps(issue.to_dict(), indent=2))
        return

    typer.echo(f"Issue Key: {issue.key}")
    typer.echo(f"Summary: {issue.summary}")
    typer.echo(f"Status: {issue.status or ''}")
    typer.echo(f"Type: {issue.issue_type or ''}")
    typer.echo(f"Assignee: {issue.assignee or 'Unassigned'}")


def render_comment_added(issue_key: str, fmt: OutputFormat, quiet: bool) -> None:
    if quiet:
        typer.echo(issue_key)
        return
    if fmt is OutputFormat.JSON:
        typer.echo(json.dumps({"issue": issue_key, "comment_added": True}, indent=2))
        return
    typer.echo(f"Comment added to {issue_key}.")


def render_issue_updated(issue_key: str, fmt: OutputFormat, quiet: bool) -> None:
    if quiet:
        typer.echo(issue_key)
        return
    if fmt is OutputFormat.JSON:
        typer.echo(json.dumps({"issue": issue_key, "updated": True}, indent=2))
        return
    typer.echo(f"Issue {issue_key} updated.")


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
