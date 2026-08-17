"""Posts adaptive-card messages to a Microsoft Teams incoming webhook.

Unrelated to Jira - this hits an arbitrary webhook URL directly with no
authentication, matching the legacy `devops-jrmt post-teams` command.
"""

from __future__ import annotations

import httpx

from jira_cli.client.exceptions import NetworkError


def post_teams_message(webhook: str, message: str, timeout: float = 30.0) -> None:
    card = {
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "type": "AdaptiveCard",
                    "version": "1.0",
                    "body": [{"type": "TextBlock", "text": message}],
                },
            }
        ]
    }

    try:
        response = httpx.post(webhook, json=card, timeout=timeout)
    except httpx.RequestError as exc:
        raise NetworkError(f"Network error posting to Teams webhook: {exc}") from exc

    if response.status_code >= 300:
        raise NetworkError(
            f"Teams webhook returned HTTP {response.status_code}: {response.text}"
        )
