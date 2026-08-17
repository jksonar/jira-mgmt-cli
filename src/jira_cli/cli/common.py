"""Shared CLI option definitions and the release-service factory used by every command."""

from __future__ import annotations

from typing import Annotated

import typer

from jira_cli.client.jira_client import JiraClient
from jira_cli.config.settings import Settings
from jira_cli.services.release_service import ReleaseService
from jira_cli.utils.logger import configure_logging, get_logger, mask_secret
from jira_cli.utils.output import OutputFormat

OutputOption = Annotated[
    OutputFormat,
    typer.Option("--output", "-o", help="Output format: table or json."),
]
QuietOption = Annotated[
    bool,
    typer.Option("--quiet", "-q", help="Print only the resulting ID (for scripting)."),
]
DryRunOption = Annotated[
    bool,
    typer.Option("--dry-run", help="Show what would happen without making changes."),
]
VerboseOption = Annotated[
    bool,
    typer.Option("--verbose", "-v", help="Enable debug logging."),
]

_logger = get_logger("cli")


def get_release_service(verbose: bool) -> ReleaseService:
    configure_logging(verbose)
    settings = Settings.load()
    mask_secret(settings.jira_api_token)
    _logger.debug("Jira URL: %s", settings.jira_url)
    client = JiraClient(settings)
    return ReleaseService(client)
