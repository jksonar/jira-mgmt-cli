"""`jira-cli artifact ...` command group: upload build artifacts to Jira issues."""

from __future__ import annotations

from typing import Annotated

import typer

from jira_cli.cli.common import (
    DryRunOption,
    OutputOption,
    QuietOption,
    VerboseOption,
    get_artifact_service,
    get_issue_service,
)
from jira_cli.utils.output import (
    OutputFormat,
    render_artifact_upload,
    render_attachment_metadata,
    render_dry_run,
)
from jira_cli.utils.validators import validate_issue_key

artifact_app = typer.Typer(help="Upload build artifacts to Jira issues.")


def _upload_comment(filenames: list[str], build_number: str | None, commit: str | None, environment: str | None) -> str:
    lines = ["Artifact uploaded successfully.", ""]
    lines.extend(f"Name: {name}" for name in filenames)
    if build_number is not None:
        lines.append(f"Build: {build_number}")
    if commit is not None:
        lines.append(f"Commit: {commit}")
    if environment is not None:
        lines.append(f"Environment: {environment}")
    return "\n".join(lines)


@artifact_app.command("upload")
def upload_artifact(
    issue_key: Annotated[
        str, typer.Argument(callback=validate_issue_key, help="Issue key, e.g. PROJ-123.")
    ],
    file: Annotated[
        list[str], typer.Option("--file", help="Path to a file to upload. Repeat for multiple files.")
    ],
    build_number: Annotated[
        str | None, typer.Option("--build-number", help="CI build number.")
    ] = None,
    environment: Annotated[
        str | None, typer.Option("--environment", help="Target environment, e.g. UAT.")
    ] = None,
    commit: Annotated[str | None, typer.Option("--commit", help="Source commit hash.")] = None,
    comment: Annotated[
        bool,
        typer.Option("--comment/--no-comment", help="Add a Jira comment summarizing the upload."),
    ] = True,
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    dry_run: DryRunOption = False,
    verbose: VerboseOption = False,
) -> None:
    if not file:
        raise typer.BadParameter("At least one --file must be provided.")

    if dry_run:
        fields = {"Issue": issue_key, "Files": ", ".join(file)}
        if build_number is not None:
            fields["Build"] = build_number
        if commit is not None:
            fields["Commit"] = commit
        if environment is not None:
            fields["Environment"] = environment
        render_dry_run("Upload Jira Artifact", fields)
        return

    artifact_service = get_artifact_service(verbose)
    attachments = artifact_service.upload_multiple_artifacts(issue_key, file)

    if comment:
        issue_service = get_issue_service(verbose)
        message = _upload_comment(
            [a.filename for a in attachments], build_number, commit, environment
        )
        issue_service.add_comment(issue_key, message)

    render_artifact_upload(issue_key, attachments, output, quiet)


@artifact_app.command("metadata")
def attachment_metadata(
    attachment_id: Annotated[str, typer.Argument(help="Attachment ID.")],
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    verbose: VerboseOption = False,
) -> None:
    service = get_artifact_service(verbose)
    attachment = service.get_attachment_metadata(attachment_id)
    render_attachment_metadata(attachment, output, quiet)
