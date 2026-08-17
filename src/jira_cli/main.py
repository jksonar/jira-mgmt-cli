"""Jira CLI entry point."""

from __future__ import annotations

import typer

from jira_cli.cli.config import config_app
from jira_cli.cli.release import release_app
from jira_cli.client.exceptions import JiraCliError
from jira_cli.utils.output import print_error

app = typer.Typer(name="jira-cli", help="Jira automation CLI.", add_completion=False)
app.add_typer(release_app, name="release")
app.add_typer(config_app, name="config")


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
