"""`jira-cli release ...` command group: manage Jira releases (project versions)."""

from __future__ import annotations

from typing import Annotated

import typer

from jira_cli.cli.common import (
    DryRunOption,
    OutputOption,
    QuietOption,
    VerboseOption,
    get_release_service,
)
from jira_cli.client.exceptions import ValidationError
from jira_cli.utils.output import (
    OutputFormat,
    render_current_release,
    render_deleted,
    render_dry_run,
    render_next_release,
    render_next_release_dry_run,
    render_release,
    render_release_list,
)
from jira_cli.utils.validators import (
    validate_date_string,
    validate_project_key,
    validate_release_name,
)

release_app = typer.Typer(help="Manage Jira releases (project versions).")

_NO_VALID_RELEASE_DETAILS = "Expected format:\nYY.MM.DD\n\nExample:\n26.08.31"


@release_app.command("current")
def current_release(
    project: Annotated[
        str, typer.Option("--project", callback=validate_project_key, help="Project key.")
    ],
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    verbose: VerboseOption = False,
) -> None:
    service = get_release_service(verbose)
    release = service.get_current_release(project)
    if release is None:
        raise ValidationError(
            "No valid CalVer release found.", details=_NO_VALID_RELEASE_DETAILS
        )
    render_current_release(project, release, output, quiet)


@release_app.command("next")
def next_release(
    project: Annotated[
        str, typer.Option("--project", callback=validate_project_key, help="Project key.")
    ],
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    dry_run: DryRunOption = False,
    verbose: VerboseOption = False,
) -> None:
    service = get_release_service(verbose)
    plan = service.plan_next_release(project, create=not dry_run)
    if dry_run:
        render_next_release_dry_run(plan, output, quiet)
        return
    render_next_release(plan, output, quiet)


@release_app.command("list")
def list_releases(
    project: Annotated[
        str, typer.Option("--project", callback=validate_project_key, help="Project key.")
    ],
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    verbose: VerboseOption = False,
) -> None:
    service = get_release_service(verbose)
    releases = service.list_releases(project)
    render_release_list(releases, output, quiet)


@release_app.command("get")
def get_release(
    version_id: Annotated[str, typer.Argument(help="Release/version ID.")],
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    verbose: VerboseOption = False,
) -> None:
    service = get_release_service(verbose)
    release = service.get_release(version_id)
    render_release(release, output, quiet)


@release_app.command("create")
def create_release(
    project: Annotated[
        str, typer.Option("--project", callback=validate_project_key, help="Project key.")
    ],
    name: Annotated[
        str,
        typer.Option(
            "--name",
            "--version",
            callback=validate_release_name,
            help="Release name/version, e.g. 26.08.31.",
        ),
    ],
    description: Annotated[
        str | None, typer.Option("--description", help="Release description.")
    ] = None,
    start_date: Annotated[
        str | None,
        typer.Option("--start-date", callback=validate_date_string, help="YYYY-MM-DD."),
    ] = None,
    release_date: Annotated[
        str | None,
        typer.Option("--release-date", callback=validate_date_string, help="YYYY-MM-DD."),
    ] = None,
    released: Annotated[
        bool, typer.Option("--released", help="Mark the release as already released.")
    ] = False,
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    dry_run: DryRunOption = False,
    verbose: VerboseOption = False,
) -> None:
    if dry_run:
        fields = {"Project": project, "Version": name}
        if description is not None:
            fields["Description"] = description
        if release_date is not None:
            fields["Release Date"] = release_date
        render_dry_run("Create Jira Release", fields)
        return

    service = get_release_service(verbose)
    release = service.create_release(
        project=project,
        name=name,
        description=description,
        start_date=start_date,
        release_date=release_date,
        released=released,
    )
    render_release(release, output, quiet)


@release_app.command("update")
def update_release(
    version_id: Annotated[str, typer.Argument(help="Release/version ID.")],
    name: Annotated[str | None, typer.Option("--name", help="New release name.")] = None,
    description: Annotated[
        str | None, typer.Option("--description", help="New description.")
    ] = None,
    start_date: Annotated[
        str | None,
        typer.Option("--start-date", callback=validate_date_string, help="YYYY-MM-DD."),
    ] = None,
    release_date: Annotated[
        str | None,
        typer.Option("--release-date", callback=validate_date_string, help="YYYY-MM-DD."),
    ] = None,
    released: Annotated[
        bool | None, typer.Option("--released", help="Set released status.")
    ] = None,
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    dry_run: DryRunOption = False,
    verbose: VerboseOption = False,
) -> None:
    fields = {
        "name": name,
        "description": description,
        "start_date": start_date,
        "release_date": release_date,
        "released": released,
    }
    if all(value is None for value in fields.values()):
        raise typer.BadParameter("At least one field must be provided to update.")

    if dry_run:
        banner_fields = {"Release": version_id}
        if name is not None:
            banner_fields["Name"] = name
        if description is not None:
            banner_fields["Description"] = description
        if start_date is not None:
            banner_fields["Start Date"] = start_date
        if release_date is not None:
            banner_fields["Release Date"] = release_date
        if released is not None:
            banner_fields["Released"] = str(released)
        render_dry_run("Update Jira Release", banner_fields)
        return

    service = get_release_service(verbose)
    release = service.update_release(
        version_id,
        name=name,
        description=description,
        start_date=start_date,
        release_date=release_date,
        released=released,
    )
    render_release(release, output, quiet)


@release_app.command("publish")
def publish_release(
    version_id: Annotated[str, typer.Argument(help="Release/version ID.")],
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    dry_run: DryRunOption = False,
    verbose: VerboseOption = False,
) -> None:
    if dry_run:
        render_dry_run("Publish Jira Release", {"Release": version_id})
        return

    service = get_release_service(verbose)
    release = service.publish_release(version_id)
    render_release(release, output, quiet)


@release_app.command("archive")
def archive_release(
    version_id: Annotated[str, typer.Argument(help="Release/version ID.")],
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    dry_run: DryRunOption = False,
    verbose: VerboseOption = False,
) -> None:
    if dry_run:
        render_dry_run("Archive Jira Release", {"Release": version_id})
        return

    service = get_release_service(verbose)
    release = service.archive_release(version_id)
    render_release(release, output, quiet)


@release_app.command("delete")
def delete_release(
    version_id: Annotated[str, typer.Argument(help="Release/version ID.")],
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    dry_run: DryRunOption = False,
    verbose: VerboseOption = False,
) -> None:
    if dry_run:
        render_dry_run("Delete Jira Release", {"Release": version_id})
        return

    service = get_release_service(verbose)
    service.delete_release(version_id)
    render_deleted(version_id, output, quiet)
