"""`jira-cli config ...` command group: configuration/connectivity utilities."""

from __future__ import annotations

import json

import typer

from jira_cli.cli.common import OutputOption, QuietOption, VerboseOption
from jira_cli.client.jira_client import JiraClient
from jira_cli.config.settings import Settings
from jira_cli.utils.logger import configure_logging, get_logger, mask_secret
from jira_cli.utils.output import OutputFormat

config_app = typer.Typer(help="Configuration and connectivity utilities.")

_logger = get_logger("cli")


@config_app.command("check")
def check(
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    verbose: VerboseOption = False,
) -> None:
    configure_logging(verbose)
    settings = Settings.load()
    mask_secret(settings.jira_api_token)
    _logger.debug("Jira URL: %s", settings.jira_url)

    with JiraClient(settings) as client:
        me = client.get("/myself")

    display_name = me.get("displayName", "")
    email = me.get("emailAddress", settings.jira_email)

    if quiet:
        typer.echo(email)
        return
    if output is OutputFormat.JSON:
        typer.echo(json.dumps({"connected": True, "displayName": display_name, "emailAddress": email}, indent=2))
        return
    typer.echo(f"Connected to Jira as {display_name} ({email})")
