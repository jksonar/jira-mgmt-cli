"""`jira-cli project ...` command group: Jira project information."""

from __future__ import annotations

from typing import Annotated

import typer

from jira_cli.cli.common import OutputOption, QuietOption, VerboseOption, get_project_service
from jira_cli.utils.output import OutputFormat, render_project, render_project_list
from jira_cli.utils.validators import validate_project_key

project_app = typer.Typer(help="Jira project information.")


@project_app.command("list")
def list_projects(
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    verbose: VerboseOption = False,
) -> None:
    service = get_project_service(verbose)
    projects = service.list_projects()
    render_project_list(projects, output, quiet)


@project_app.command("get")
def get_project(
    project: Annotated[str, typer.Argument(callback=validate_project_key, help="Project key.")],
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    verbose: VerboseOption = False,
) -> None:
    service = get_project_service(verbose)
    result = service.get_project(project)
    render_project(result, output, quiet)
