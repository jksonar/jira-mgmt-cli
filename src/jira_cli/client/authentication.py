"""Builds the HTTP auth used against Jira Cloud (email + API token, HTTP Basic)."""

from __future__ import annotations

import httpx

from jira_cli.config.settings import Settings


def build_basic_auth(settings: Settings) -> httpx.BasicAuth:
    return httpx.BasicAuth(settings.jira_email, settings.jira_api_token)
