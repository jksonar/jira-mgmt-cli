"""Jira CLI entry point."""

from __future__ import annotations

from typing import Annotated

import typer

from jira_cli.cli.artifact import artifact_app
from jira_cli.cli.common import set_verify_ssl
from jira_cli.cli.config import config_app
from jira_cli.cli.issue import issue_app
from jira_cli.cli.notify import notify_app
from jira_cli.cli.project import project_app
from jira_cli.cli.release import release_app
from jira_cli.client.exceptions import JiraCliError
from jira_cli.utils.output import print_error

app = typer.Typer(name="jira-cli", help="Jira automation CLI.", add_completion=False)
app.add_typer(project_app, name="project")
app.add_typer(issue_app, name="issue")
app.add_typer(release_app, name="release")
app.add_typer(artifact_app, name="artifact")
app.add_typer(config_app, name="config")
app.add_typer(notify_app, name="notify")


@app.callback()
def main(
    no_verify_ssl: Annotated[
        bool,
        typer.Option(
            "--no-verify-ssl",
            help="Disable TLS certificate verification (development only).",
        ),
    ] = False,
) -> None:
    if no_verify_ssl:
        typer.echo(
            "WARNING: TLS certificate verification is disabled (--no-verify-ssl). "
            "Do not use against production Jira instances.",
            err=True,
        )
    set_verify_ssl(not no_verify_ssl)


def cli() -> None:
    try:
        app()
    except JiraCliError as exc:
        print_error(exc)
        raise SystemExit(exc.exit_code)
    except Exception as exc:  # noqa: BLE001 - final safety net, mapped to exit code 1
        typer.echo(f"ERROR: {exc}", err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
