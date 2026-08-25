"""Table/JSON/quiet rendering and dry-run/error banners."""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Callable

import typer

from jira_cli.client.exceptions import JiraCliError
from jira_cli.models.artifact import Attachment
from jira_cli.models.issue import Issue
from jira_cli.models.project import Project
from jira_cli.models.release import (
    CurrentRelease,
    FinalizeReleasePlan,
    NextReleasePlan,
    RenameBasePlan,
    RenameByTokenResult,
    Release,
)


class OutputFormat(str, Enum):
    TABLE = "table"
    JSON = "json"
    VERSION = "version"
    BRANCH_NAME = "branch-name"


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


def render(
    fmt: OutputFormat,
    quiet: bool,
    *,
    quiet_fn: Callable[[], None],
    json_fn: Callable[[], Any],
    text_fn: Callable[[], None],
) -> None:
    """Shared quiet -> JSON -> text three-way branch used by most renderers below."""
    if quiet:
        quiet_fn()
        return
    if fmt is OutputFormat.JSON:
        typer.echo(json.dumps(json_fn(), indent=2))
        return
    text_fn()


def render_list(
    items: list[Any],
    fmt: OutputFormat,
    quiet: bool,
    *,
    quiet_key: Callable[[Any], str],
    headers: list[str],
    row: Callable[[Any], list[str]],
) -> None:
    """Shared renderer for a list of model objects (quiet id/key, JSON to_dict list, table)."""
    render(
        fmt,
        quiet,
        quiet_fn=lambda: [typer.echo(quiet_key(item)) for item in items],
        json_fn=lambda: [item.to_dict() for item in items],
        text_fn=lambda: print_table(headers, [row(item) for item in items]),
    )


def render_action(
    quiet_value: str,
    fmt: OutputFormat,
    quiet: bool,
    *,
    json_fields: dict[str, Any],
    message: str,
) -> None:
    """Shared renderer for simple action confirmations (quiet key, JSON blob, or a message)."""
    render(
        fmt,
        quiet,
        quiet_fn=lambda: typer.echo(quiet_value),
        json_fn=lambda: json_fields,
        text_fn=lambda: typer.echo(message),
    )


def render_release_list(releases: list[Release], fmt: OutputFormat, quiet: bool) -> None:
    render_list(
        releases,
        fmt,
        quiet,
        quiet_key=lambda r: r.id,
        headers=["ID", "NAME", "RELEASE DATE", "RELEASED"],
        row=lambda r: [r.id, r.name, r.release_date or "", "yes" if r.released else "no"],
    )


def render_release(release: Release, fmt: OutputFormat, quiet: bool) -> None:
    def _text() -> None:
        typer.echo(f"Release ID: {release.id}")
        typer.echo(f"Name: {release.name}")
        if release.description:
            typer.echo(f"Description: {release.description}")
        typer.echo(f"Start Date: {release.start_date or ''}")
        typer.echo(f"Release Date: {release.release_date or ''}")
        typer.echo(f"Released: {'yes' if release.released else 'no'}")
        typer.echo(f"Archived: {'yes' if release.archived else 'no'}")

    render(
        fmt,
        quiet,
        quiet_fn=lambda: typer.echo(release.id),
        json_fn=release.to_dict,
        text_fn=_text,
    )


def render_current_release(
    project: str, current: CurrentRelease, fmt: OutputFormat, quiet: bool
) -> None:
    if quiet or fmt is OutputFormat.VERSION:
        typer.echo(current.version)
        return

    if fmt is OutputFormat.JSON:
        typer.echo(
            json.dumps(
                {
                    "project": project,
                    "version": current.version,
                    "name": current.release.name,
                    "released": current.release.released,
                },
                indent=2,
            )
        )
        return

    typer.echo("Current Jira Release")
    typer.echo("")
    typer.echo(f"Project : {project}")
    typer.echo(f"Version : {current.version}")
    typer.echo(f"Name    : {current.release.name}")
    typer.echo(f"Release : {'Released' if current.release.released else 'Unreleased'}")


def render_next_release(plan: NextReleasePlan, fmt: OutputFormat, quiet: bool) -> None:
    if quiet or fmt is OutputFormat.VERSION:
        typer.echo(plan.next_release)
        return

    if fmt is OutputFormat.BRANCH_NAME:
        typer.echo(plan.branch_name)
        return

    if fmt is OutputFormat.JSON:
        typer.echo(json.dumps(plan.to_dict(), indent=2))
        return

    status = "EXISTS" if plan.existing else "CREATED"
    typer.echo("=" * 40)
    typer.echo("JIRA NEXT RELEASE")
    typer.echo("=" * 40)
    typer.echo("")
    typer.echo(f"Project          : {plan.project}")
    if plan.system_key:
        typer.echo(f"System Key       : {plan.system_key}")
    typer.echo(f"Current Release  : {plan.previous_release}")
    typer.echo(f"Next Release     : {plan.next_release}")
    typer.echo(f"Branch Name      : {plan.branch_name}")
    typer.echo(f"Status           : {status}")
    if plan.release_id:
        typer.echo(f"Release ID       : {plan.release_id}")
    if plan.moved:
        typer.echo("Moved            : after previous release")
    if plan.renamed_previous:
        typer.echo(f"Renamed Previous : {plan.previous_release} - in Deployment")
    typer.echo("")
    typer.echo("=" * 40)


def render_next_release_dry_run(plan: NextReleasePlan, fmt: OutputFormat, quiet: bool) -> None:
    if quiet or fmt is OutputFormat.VERSION:
        typer.echo(plan.next_release)
        return

    if fmt is OutputFormat.BRANCH_NAME:
        typer.echo(plan.branch_name)
        return

    if fmt is OutputFormat.JSON:
        typer.echo(json.dumps({**plan.to_dict(), "dry_run": True}, indent=2))
        return

    typer.echo("DRY RUN")
    typer.echo("")
    typer.echo(f"Current Release : {plan.previous_release}")
    typer.echo(f"Release Date    : {plan.release_date}")
    typer.echo(f"Next Release    : {plan.next_release}")
    typer.echo(f"Branch Name     : {plan.branch_name}")
    typer.echo("")
    typer.echo("No changes will be made to Jira.")


def render_finalize_release(plan: FinalizeReleasePlan, fmt: OutputFormat, quiet: bool) -> None:
    def _text() -> None:
        if not plan.found:
            typer.echo(f"No release found for project {plan.project} matching that label.")
            return

        typer.echo("Finalize Jira Release")
        typer.echo("")
        typer.echo(f"Project      : {plan.project}")
        if plan.system_key:
            typer.echo(f"System Key   : {plan.system_key}")
        typer.echo(f"Release ID   : {plan.release_id}")
        typer.echo(f"Previous Name: {plan.previous_name}")
        typer.echo(f"New Name     : {plan.new_name}")
        if plan.stripped_release_ids:
            typer.echo(f"Stripped     : {', '.join(plan.stripped_release_ids)}")
        typer.echo(f"Released     : {'yes' if plan.released else 'no'}")

    render(
        fmt,
        quiet,
        quiet_fn=lambda: typer.echo(plan.release_id or ""),
        json_fn=plan.to_dict,
        text_fn=_text,
    )


def render_rename_base(plan: RenameBasePlan, fmt: OutputFormat, quiet: bool) -> None:
    def _text() -> None:
        typer.echo("Rename Base Release")
        typer.echo("")
        typer.echo(f"Project      : {plan.project}")
        if plan.system_key:
            typer.echo(f"System Key   : {plan.system_key}")
        typer.echo(f"Release ID   : {plan.release_id}")
        typer.echo(f"Previous Name: {plan.previous_name}")
        typer.echo(f"New Name     : {plan.new_name}")

    render(
        fmt,
        quiet,
        quiet_fn=lambda: typer.echo(plan.release_id),
        json_fn=plan.to_dict,
        text_fn=_text,
    )


def render_release_id(release: Release, fmt: OutputFormat, quiet: bool) -> None:
    if quiet or fmt is OutputFormat.VERSION:
        typer.echo(release.id)
        return

    if fmt is OutputFormat.JSON:
        typer.echo(json.dumps({"id": release.id, "name": release.name}, indent=2))
        return

    typer.echo(f"Release ID: {release.id}")
    typer.echo(f"Name: {release.name}")


def render_release_property(property_name: str, value: Any, fmt: OutputFormat, quiet: bool) -> None:
    render(
        fmt,
        quiet,
        quiet_fn=lambda: typer.echo("" if value is None else str(value)),
        json_fn=lambda: {"property": property_name, "value": value},
        text_fn=lambda: typer.echo(f"{property_name}: {value}"),
    )


def render_rename_by_token_results(
    results: list[RenameByTokenResult], fmt: OutputFormat, quiet: bool
) -> None:
    render_list(
        results,
        fmt,
        quiet,
        quiet_key=lambda r: r.id,
        headers=["ID", "ORIGINAL NAME", "NEW NAME", "UPDATED"],
        row=lambda r: [r.id, r.original_name, r.new_name, "yes" if r.updated else "no"],
    )


def render_deleted(version_id: str, fmt: OutputFormat, quiet: bool) -> None:
    render_action(
        version_id,
        fmt,
        quiet,
        json_fields={"id": version_id, "deleted": True},
        message=f"Release {version_id} deleted.",
    )


def render_project_list(projects: list[Project], fmt: OutputFormat, quiet: bool) -> None:
    render_list(
        projects,
        fmt,
        quiet,
        quiet_key=lambda p: p.key,
        headers=["ID", "KEY", "NAME", "TYPE"],
        row=lambda p: [p.id or "", p.key, p.name, p.project_type or ""],
    )


def render_project(project: Project, fmt: OutputFormat, quiet: bool) -> None:
    def _text() -> None:
        typer.echo(f"Project Key: {project.key}")
        typer.echo(f"Name: {project.name}")
        if project.lead:
            typer.echo(f"Lead: {project.lead}")
        typer.echo(f"Type: {project.project_type or ''}")

    render(
        fmt,
        quiet,
        quiet_fn=lambda: typer.echo(project.key),
        json_fn=project.to_dict,
        text_fn=_text,
    )


def render_issue_list(issues: list[Issue], fmt: OutputFormat, quiet: bool) -> None:
    render_list(
        issues,
        fmt,
        quiet,
        quiet_key=lambda i: i.key,
        headers=["KEY", "SUMMARY", "STATUS", "ASSIGNEE"],
        row=lambda i: [i.key, i.summary, i.status or "", i.assignee or ""],
    )


def render_issue(issue: Issue, fmt: OutputFormat, quiet: bool) -> None:
    def _text() -> None:
        typer.echo(f"Issue Key: {issue.key}")
        typer.echo(f"Summary: {issue.summary}")
        typer.echo(f"Status: {issue.status or ''}")
        typer.echo(f"Type: {issue.issue_type or ''}")
        typer.echo(f"Assignee: {issue.assignee or 'Unassigned'}")

    render(
        fmt,
        quiet,
        quiet_fn=lambda: typer.echo(issue.key),
        json_fn=issue.to_dict,
        text_fn=_text,
    )


def render_comment_added(issue_key: str, fmt: OutputFormat, quiet: bool) -> None:
    render_action(
        issue_key,
        fmt,
        quiet,
        json_fields={"issue": issue_key, "comment_added": True},
        message=f"Comment added to {issue_key}.",
    )


def render_issue_updated(issue_key: str, fmt: OutputFormat, quiet: bool) -> None:
    render_action(
        issue_key,
        fmt,
        quiet,
        json_fields={"issue": issue_key, "updated": True},
        message=f"Issue {issue_key} updated.",
    )


def render_issue_assigned(issue_key: str, user: str, fmt: OutputFormat, quiet: bool) -> None:
    render_action(
        issue_key,
        fmt,
        quiet,
        json_fields={"issue": issue_key, "assignee": user},
        message=f"Issue {issue_key} assigned to {user}.",
    )


def render_issue_transitioned(issue_key: str, status: str, fmt: OutputFormat, quiet: bool) -> None:
    render_action(
        issue_key,
        fmt,
        quiet,
        json_fields={"issue": issue_key, "status": status},
        message=f"Issue {issue_key} transitioned to {status}.",
    )


def render_issue_deleted(issue_key: str, fmt: OutputFormat, quiet: bool) -> None:
    render_action(
        issue_key,
        fmt,
        quiet,
        json_fields={"issue": issue_key, "deleted": True},
        message=f"Issue {issue_key} deleted.",
    )


def render_artifact_upload(
    issue_key: str, attachments: list[Attachment], fmt: OutputFormat, quiet: bool
) -> None:
    def _quiet() -> None:
        for attachment in attachments:
            typer.echo(attachment.id)

    def _text() -> None:
        typer.echo("Artifact uploaded successfully.")
        typer.echo("")
        for attachment in attachments:
            typer.echo(f"Name: {attachment.filename}")
            typer.echo(f"Attachment ID: {attachment.id}")
            typer.echo(f"Size: {attachment.size} bytes")
            typer.echo("")

    render(
        fmt,
        quiet,
        quiet_fn=_quiet,
        json_fn=lambda: {"issue": issue_key, "attachments": [a.to_dict() for a in attachments]},
        text_fn=_text,
    )


def render_attachment_metadata(attachment: Attachment, fmt: OutputFormat, quiet: bool) -> None:
    def _text() -> None:
        typer.echo(f"Attachment ID: {attachment.id}")
        typer.echo(f"Name: {attachment.filename}")
        typer.echo(f"Size: {attachment.size} bytes")
        if attachment.mime_type:
            typer.echo(f"MIME Type: {attachment.mime_type}")
        if attachment.created:
            typer.echo(f"Created: {attachment.created}")

    render(
        fmt,
        quiet,
        quiet_fn=lambda: typer.echo(attachment.id),
        json_fn=attachment.to_dict,
        text_fn=_text,
    )


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
