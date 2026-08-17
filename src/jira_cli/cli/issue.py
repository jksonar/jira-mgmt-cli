"""`jira-cli issue ...` command group: Jira issue management."""

from __future__ import annotations

from typing import Annotated

import typer

from jira_cli.cli.common import (
    DryRunOption,
    OutputOption,
    QuietOption,
    VerboseOption,
    get_issue_service,
)
from jira_cli.utils.output import (
    OutputFormat,
    render_comment_added,
    render_dry_run,
    render_issue,
    render_issue_list,
    render_issue_updated,
)
from jira_cli.utils.validators import validate_issue_key, validate_jql

issue_app = typer.Typer(help="Jira issue management.")


@issue_app.command("get")
def get_issue(
    issue_key: Annotated[str, typer.Argument(callback=validate_issue_key, help="Issue key, e.g. PROJ-123.")],
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    verbose: VerboseOption = False,
) -> None:
    service = get_issue_service(verbose)
    issue = service.get_issue(issue_key)
    render_issue(issue, output, quiet)


@issue_app.command("search")
def search_issues(
    jql: Annotated[str, typer.Option("--jql", callback=validate_jql, help="JQL query.")],
    max_results: Annotated[
        int, typer.Option("--max-results", help="Maximum number of issues to return.")
    ] = 50,
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    verbose: VerboseOption = False,
) -> None:
    service = get_issue_service(verbose)
    issues = service.search_issues(jql, max_results=max_results)
    render_issue_list(issues, output, quiet)


@issue_app.command("comment")
def comment_issue(
    issue_key: Annotated[str, typer.Argument(callback=validate_issue_key, help="Issue key, e.g. PROJ-123.")],
    message: Annotated[str, typer.Option("--message", help="Comment text.")],
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    dry_run: DryRunOption = False,
    verbose: VerboseOption = False,
) -> None:
    if dry_run:
        render_dry_run("Add Jira Comment", {"Issue": issue_key, "Message": message})
        return

    service = get_issue_service(verbose)
    service.add_comment(issue_key, message)
    render_comment_added(issue_key, output, quiet)


@issue_app.command("update")
def update_issue(
    issue_key: Annotated[str, typer.Argument(callback=validate_issue_key, help="Issue key, e.g. PROJ-123.")],
    summary: Annotated[str | None, typer.Option("--summary", help="New issue summary.")] = None,
    description: Annotated[
        str | None, typer.Option("--description", help="New issue description.")
    ] = None,
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    dry_run: DryRunOption = False,
    verbose: VerboseOption = False,
) -> None:
    if summary is None and description is None:
        raise typer.BadParameter("At least one field must be provided to update.")

    if dry_run:
        fields = {"Issue": issue_key}
        if summary is not None:
            fields["Summary"] = summary
        if description is not None:
            fields["Description"] = description
        render_dry_run("Update Jira Issue", fields)
        return

    service = get_issue_service(verbose)
    service.update_issue(issue_key, summary=summary, description=description)
    render_issue_updated(issue_key, output, quiet)
