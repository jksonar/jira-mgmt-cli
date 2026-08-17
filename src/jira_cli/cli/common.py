"""Shared CLI option definitions and the release-service factory used by every command."""

from __future__ import annotations

from typing import Annotated

import typer

from jira_cli.client.jira_client import JiraClient
from jira_cli.config.settings import Settings
from jira_cli.services.issue_service import IssueService
from jira_cli.services.project_service import ProjectService
from jira_cli.services.release_service import ReleaseService
from jira_cli.utils.logger import configure_logging, get_logger, mask_secret
from jira_cli.utils.output import OutputFormat

OutputOption = Annotated[
    OutputFormat,
    typer.Option("--output", "-o", help="Output format: table, json, or version."),
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


def _build_client(verbose: bool) -> JiraClient:
    configure_logging(verbose)
    settings = Settings.load()
    mask_secret(settings.jira_api_token)
    _logger.debug("Jira URL: %s", settings.jira_url)
    return JiraClient(settings)


def get_release_service(verbose: bool) -> ReleaseService:
    return ReleaseService(_build_client(verbose))


def get_project_service(verbose: bool) -> ProjectService:
    return ProjectService(_build_client(verbose))


def get_issue_service(verbose: bool) -> IssueService:
    return IssueService(_build_client(verbose))
