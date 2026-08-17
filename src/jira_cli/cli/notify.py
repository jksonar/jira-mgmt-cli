"""`jira-cli notify ...` command group: notifications to external services."""

from __future__ import annotations

from typing import Annotated

import typer

from jira_cli.cli.common import DryRunOption
from jira_cli.services.teams_service import post_teams_message
from jira_cli.utils.output import render_dry_run

notify_app = typer.Typer(help="Send notifications to external services.")


@notify_app.command("teams")
def post_teams(
    message: Annotated[str, typer.Option("--message", "-m", help="Message text.")],
    webhook: Annotated[str, typer.Option("--webhook", "-wh", help="Teams webhook URL.")],
    dry_run: DryRunOption = False,
) -> None:
    if dry_run:
        render_dry_run("Post to MS Teams", {"Message": message, "Webhook": webhook})
        return

    post_teams_message(webhook, message)
    typer.echo("Message posted to Microsoft Teams.")
