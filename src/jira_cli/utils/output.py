"""Table/JSON/quiet rendering and dry-run/error banners."""

from __future__ import annotations

import json
from enum import Enum
from typing import Any

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
    if quiet:
        typer.echo(plan.release_id or "")
        return

    if fmt is OutputFormat.JSON:
        typer.echo(json.dumps(plan.to_dict(), indent=2))
        return

    if not plan.found:
        typer.echo(f"No release found for project {plan.project} matching that label.")
        return

    typer.echo("Finalize Jira Release")
    typer.echo("")
    typer.echo(f"Project      : {plan.project}")
    typer.echo(f"Release ID   : {plan.release_id}")
    typer.echo(f"Previous Name: {plan.previous_name}")
    typer.echo(f"New Name     : {plan.new_name}")
    if plan.stripped_release_ids:
        typer.echo(f"Stripped     : {', '.join(plan.stripped_release_ids)}")
    typer.echo(f"Released     : {'yes' if plan.released else 'no'}")


def render_rename_base(plan: RenameBasePlan, fmt: OutputFormat, quiet: bool) -> None:
    if quiet:
        typer.echo(plan.release_id)
        return

    if fmt is OutputFormat.JSON:
        typer.echo(json.dumps(plan.to_dict(), indent=2))
        return

    typer.echo("Rename Base Release")
    typer.echo("")
    typer.echo(f"Project      : {plan.project}")
    typer.echo(f"Release ID   : {plan.release_id}")
    typer.echo(f"Previous Name: {plan.previous_name}")
    typer.echo(f"New Name     : {plan.new_name}")


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
    if quiet:
        typer.echo("" if value is None else str(value))
        return

    if fmt is OutputFormat.JSON:
        typer.echo(json.dumps({"property": property_name, "value": value}, indent=2))
        return

    typer.echo(f"{property_name}: {value}")


def render_rename_by_token_results(
    results: list[RenameByTokenResult], fmt: OutputFormat, quiet: bool
) -> None:
    if quiet:
        for result in results:
            typer.echo(result.id)
        return

    if fmt is OutputFormat.JSON:
        typer.echo(json.dumps([r.to_dict() for r in results], indent=2))
        return

    rows = [
        [r.id, r.original_name, r.new_name, "yes" if r.updated else "no"] for r in results
    ]
    print_table(["ID", "ORIGINAL NAME", "NEW NAME", "UPDATED"], rows)


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


def render_issue_assigned(issue_key: str, user: str, fmt: OutputFormat, quiet: bool) -> None:
    if quiet:
        typer.echo(issue_key)
        return
    if fmt is OutputFormat.JSON:
        typer.echo(json.dumps({"issue": issue_key, "assignee": user}, indent=2))
        return
    typer.echo(f"Issue {issue_key} assigned to {user}.")


def render_issue_transitioned(issue_key: str, status: str, fmt: OutputFormat, quiet: bool) -> None:
    if quiet:
        typer.echo(issue_key)
        return
    if fmt is OutputFormat.JSON:
        typer.echo(json.dumps({"issue": issue_key, "status": status}, indent=2))
        return
    typer.echo(f"Issue {issue_key} transitioned to {status}.")


def render_issue_deleted(issue_key: str, fmt: OutputFormat, quiet: bool) -> None:
    if fmt is OutputFormat.JSON and not quiet:
        typer.echo(json.dumps({"issue": issue_key, "deleted": True}, indent=2))
        return
    typer.echo(f"Issue {issue_key} deleted." if not quiet else issue_key)


def render_artifact_upload(
    issue_key: str, attachments: list[Attachment], fmt: OutputFormat, quiet: bool
) -> None:
    if quiet:
        for attachment in attachments:
            typer.echo(attachment.id)
        return

    if fmt is OutputFormat.JSON:
        typer.echo(
            json.dumps(
                {"issue": issue_key, "attachments": [a.to_dict() for a in attachments]},
                indent=2,
            )
        )
        return

    typer.echo("Artifact uploaded successfully.")
    typer.echo("")
    for attachment in attachments:
        typer.echo(f"Name: {attachment.filename}")
        typer.echo(f"Attachment ID: {attachment.id}")
        typer.echo(f"Size: {attachment.size} bytes")
        typer.echo("")


def render_attachment_metadata(attachment: Attachment, fmt: OutputFormat, quiet: bool) -> None:
    if quiet:
        typer.echo(attachment.id)
        return

    if fmt is OutputFormat.JSON:
        typer.echo(json.dumps(attachment.to_dict(), indent=2))
        return

    typer.echo(f"Attachment ID: {attachment.id}")
    typer.echo(f"Name: {attachment.filename}")
    typer.echo(f"Size: {attachment.size} bytes")
    if attachment.mime_type:
        typer.echo(f"MIME Type: {attachment.mime_type}")
    if attachment.created:
        typer.echo(f"Created: {attachment.created}")


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
