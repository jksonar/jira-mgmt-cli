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
    render_finalize_release,
    render_next_release,
    render_next_release_dry_run,
    render_release,
    render_release_id,
    render_release_list,
    render_release_property,
    render_rename_base,
    render_rename_by_token_results,
)
from jira_cli.utils.validators import (
    validate_date_string,
    validate_project_key,
    validate_release_name,
)
from jira_cli.utils.version_name import clean_version_name

release_app = typer.Typer(help="Manage Jira releases (project versions).")

_NO_VALID_RELEASE_DETAILS = "Expected format:\nMAJOR.MINOR.PATCH\n\nExample:\n25.10.3"


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
    current = service.get_current_release(project)
    if current is None:
        raise ValidationError(
            "No valid release found.", details=_NO_VALID_RELEASE_DETAILS
        )
    render_current_release(project, current, output, quiet)


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


@release_app.command("finalize")
def finalize_release(
    project: Annotated[
        str, typer.Option("--project", callback=validate_project_key, help="Project key.")
    ],
    to_label: Annotated[
        str,
        typer.Option(
            "--to-label", help='Label to apply to the release name, e.g. "on DEV".'
        ),
    ],
    from_label: Annotated[
        str,
        typer.Option(
            "--from-label", help="Label currently on the release being finalized."
        ),
    ] = "in Deployment",
    strip_token: Annotated[
        str | None,
        typer.Option(
            "--strip-token",
            help="If set, strip this token from every other release name first, "
            "so only the newly-finalized release carries it.",
        ),
    ] = None,
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    dry_run: DryRunOption = False,
    verbose: VerboseOption = False,
) -> None:
    service = get_release_service(verbose)
    plan = service.finalize_release(
        project,
        to_label=to_label,
        from_label=from_label,
        strip_token=strip_token,
        create=not dry_run,
    )
    render_finalize_release(plan, output, quiet)


@release_app.command("rename-base")
def rename_base_release(
    project: Annotated[
        str, typer.Option("--project", callback=validate_project_key, help="Project key.")
    ],
    version: Annotated[
        str, typer.Option("--version", help="Plain version to reset the release name to.")
    ],
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    dry_run: DryRunOption = False,
    verbose: VerboseOption = False,
) -> None:
    service = get_release_service(verbose)
    plan = service.rename_base_release(project, version, create=not dry_run)
    render_rename_base(plan, output, quiet)


@release_app.command("get-by-name")
def get_release_by_name(
    project: Annotated[
        str, typer.Option("--project", callback=validate_project_key, help="Project key.")
    ],
    name: Annotated[
        str, typer.Option("--name", help="Substring to match in release names (case-sensitive).")
    ],
    release_index: Annotated[
        int,
        typer.Option(
            "--release-index",
            help="0-based index among matches sorted by release date, newest first.",
        ),
    ] = 0,
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    verbose: VerboseOption = False,
) -> None:
    service = get_release_service(verbose)
    release = service.get_release_by_name(project, name, release_index=release_index)
    render_release_id(release, output, quiet)


@release_app.command("latest-released")
def latest_released_release(
    project: Annotated[
        str, typer.Option("--project", callback=validate_project_key, help="Project key.")
    ],
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    verbose: VerboseOption = False,
) -> None:
    service = get_release_service(verbose)
    release = service.get_latest_released_release(project)
    render_release_id(release, output, quiet)


@release_app.command("get-property")
def get_release_property(
    project: Annotated[
        str, typer.Option("--project", callback=validate_project_key, help="Project key.")
    ],
    version_id: Annotated[str, typer.Option("--version-id", help="Release/version ID.")],
    property_name: Annotated[
        str,
        typer.Option(
            "--property", help='Raw Jira field name, e.g. "name", "releaseDate", "released".'
        ),
    ],
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    verbose: VerboseOption = False,
) -> None:
    service = get_release_service(verbose)
    value = service.get_release_property(project, version_id, property_name)
    render_release_property(property_name, value, output, quiet)


@release_app.command("find")
def find_releases(
    project: Annotated[
        str, typer.Option("--project", callback=validate_project_key, help="Project key.")
    ],
    search: Annotated[
        str, typer.Option("--search", help="Substring to match in release names (case-insensitive).")
    ],
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    verbose: VerboseOption = False,
) -> None:
    service = get_release_service(verbose)
    releases = service.get_versions_by_name(project, search)
    render_release_list(releases, output, quiet)


@release_app.command("move")
def move_release(
    id: Annotated[str, typer.Option("--id", help="Version ID to move.")],
    after_id: Annotated[
        str, typer.Option("--after-id", help="Version ID to position the moved version after.")
    ],
    project: Annotated[
        str | None,
        typer.Option("--project", help="Unused; accepted for pipeline compatibility."),
    ] = None,
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    dry_run: DryRunOption = False,
    verbose: VerboseOption = False,
) -> None:
    if dry_run:
        render_dry_run("Move Jira Release", {"Version": id, "After": after_id})
        return

    service = get_release_service(verbose)
    release = service.move_release(id, after_id)
    render_release(release, output, quiet)


@release_app.command("rename-by-token")
def rename_by_token(
    project: Annotated[
        str, typer.Option("--project", callback=validate_project_key, help="Project key.")
    ],
    search: Annotated[
        str, typer.Option("--search", help="Substring to match in release names (case-insensitive).")
    ],
    token: Annotated[
        str | None,
        typer.Option(
            "--token", help="Token to strip from matched release names (defaults to --search)."
        ),
    ] = None,
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    dry_run: DryRunOption = False,
    verbose: VerboseOption = False,
) -> None:
    if dry_run:
        render_dry_run(
            "Rename Jira Releases By Token",
            {"Search": search, "Token": token or search},
        )
        return

    service = get_release_service(verbose)
    results = service.rename_versions_by_token(project, search, token)
    render_rename_by_token_results(results, output, quiet)


@release_app.command("clean-name")
def clean_name(
    name: Annotated[str, typer.Option("--name", help="Raw release name.")],
    token: Annotated[str, typer.Option("--token", help="Token to strip from the name.")],
) -> None:
    typer.echo(clean_version_name(name, token))


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
