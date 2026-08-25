"""`jira-cli config ...` command group: configuration/connectivity utilities."""

from __future__ import annotations

import json

import typer

from jira_cli.cli.common import OutputOption, QuietOption, VerboseOption, build_client
from jira_cli.config.settings import Settings
from jira_cli.utils.output import OutputFormat, print_table

config_app = typer.Typer(help="Configuration and connectivity utilities.")


@config_app.command("check")
def check(
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    verbose: VerboseOption = False,
) -> None:
    settings = Settings.load()

    with build_client(verbose) as client:
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


@config_app.command("test")
def test_connection(
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    verbose: VerboseOption = False,
) -> None:
    settings = Settings.load()

    with build_client(verbose) as client:
        client.get("/myself")

    if quiet:
        typer.echo(settings.jira_email)
        return
    if output is OutputFormat.JSON:
        typer.echo(
            json.dumps(
                {
                    "connected": True,
                    "jira_url": settings.jira_url,
                    "user": settings.jira_email,
                },
                indent=2,
            )
        )
        return
    typer.echo("Jira connection successful.")
    typer.echo("")
    typer.echo(f"Jira URL : {settings.jira_url}")
    typer.echo(f"User     : {settings.jira_email}")
    typer.echo("Status   : Connected")


@config_app.command("field-configurations")
def field_configurations(
    output: OutputOption = OutputFormat.TABLE,
    quiet: QuietOption = False,
    verbose: VerboseOption = False,
) -> None:
    """List Jira field configurations. Requires Jira global admin permission."""
    with build_client(verbose) as client:
        data = client.get("/fieldconfiguration")

    values = (data or {}).get("values", [])

    if quiet:
        for value in values:
            typer.echo(str(value.get("id", "")))
        return
    if output is OutputFormat.JSON:
        typer.echo(json.dumps(data, indent=2))
        return

    rows = [
        [str(value.get("id", "")), value.get("name", ""), value.get("description", "")]
        for value in values
    ]
    print_table(["ID", "NAME", "DESCRIPTION"], rows)
