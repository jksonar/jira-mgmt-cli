"""Maps issue operations onto Jira Cloud's issue and enhanced-search REST endpoints."""

from __future__ import annotations

from typing import Any

from jira_cli.client.exceptions import ValidationError
from jira_cli.client.jira_client import JiraClient
from jira_cli.models.issue import Issue

_ISSUE_FIELDS = ["summary", "status", "issuetype", "project", "assignee"]


def _text_to_adf(text: str) -> dict[str, Any]:
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text}],
            }
        ],
    }


class IssueService:
    def __init__(self, client: JiraClient) -> None:
        self._client = client

    def get_issue(self, issue_key: str) -> Issue:
        data = self._client.get(
            f"/issue/{issue_key}", params={"fields": ",".join(_ISSUE_FIELDS)}
        )
        return Issue.from_api(data)

    def search_issues(self, jql: str, max_results: int = 50) -> list[Issue]:
        body = {
            "jql": jql,
            "maxResults": max_results,
            "fields": _ISSUE_FIELDS,
        }
        data = self._client.post("/search/jql", json=body)
        issues = (data or {}).get("issues", [])
        return [Issue.from_api(i) for i in issues]

    def add_comment(self, issue_key: str, message: str) -> None:
        self._client.post(
            f"/issue/{issue_key}/comment", json={"body": _text_to_adf(message)}
        )

    def update_issue(
        self,
        issue_key: str,
        summary: str | None = None,
        description: str | None = None,
    ) -> None:
        fields: dict[str, Any] = {}
        if summary is not None:
            fields["summary"] = summary
        if description is not None:
            fields["description"] = _text_to_adf(description)

        if not fields:
            raise ValidationError("No fields provided to update.")

        self._client.put(f"/issue/{issue_key}", json={"fields": fields})
