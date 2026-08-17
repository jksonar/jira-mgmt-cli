"""Loads Jira connection settings from environment variables / .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from jira_cli.client.exceptions import ConfigurationError

_REQUIRED_VARS = ("JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN")


@dataclass(frozen=True)
class Settings:
    jira_url: str
    jira_email: str
    jira_api_token: str

    @classmethod
    def load(cls) -> "Settings":
        load_dotenv()

        values = {name: os.environ.get(name, "").strip() for name in _REQUIRED_VARS}
        missing = [name for name, value in values.items() if not value]
        if missing:
            details = "\n".join(f"- {name}" for name in _REQUIRED_VARS)
            raise ConfigurationError(
                "Jira authentication failed.",
                details=f"Please verify:\n{details}",
            )

        return cls(
            jira_url=values["JIRA_URL"].rstrip("/"),
            jira_email=values["JIRA_EMAIL"],
            jira_api_token=values["JIRA_API_TOKEN"],
        )
