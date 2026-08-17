"""Maps issue operations onto Jira Cloud's issue and enhanced-search REST endpoints."""

from __future__ import annotations

from typing import Any

from jira_cli.client.exceptions import ValidationError
from jira_cli.client.jira_client import JiraClient
from jira_cli.models.issue import Issue

_ISSUE_FIELDS = ["summary", "status", "issuetype", "project", "assignee"]

# Cascading-select custom field used to categorize tickets by service factory,
# specific to this Jira instance's schema.
_SERVICE_FACTORY_FIELD = "customfield_10829"


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

    def assign_issue(self, issue_key: str, user: str) -> None:
        """Assign `issue_key` to `user` (a Jira Cloud accountId)."""
        self._client.put(f"/issue/{issue_key}/assignee", json={"accountId": user})

    def create_issue(
        self,
        project: str,
        summary: str,
        issue_type: str,
        servicefactory: str,
        author: str,
        description: str | None = None,
    ) -> Issue:
        """Create a ticket tagged with the Service Factory cascading field,
        reported by `author` (a Jira Cloud accountId)."""
        fields: dict[str, Any] = {
            "project": {"key": project},
            "summary": summary,
            "issuetype": {"name": issue_type},
            _SERVICE_FACTORY_FIELD: {"value": "Improvements", "child": {"value": servicefactory}},
            "reporter": {"id": author},
        }
        if description is not None:
            fields["description"] = _text_to_adf(description)

        data = self._client.post("/issue", json={"fields": fields})
        return self.get_issue(data["key"])

    def delete_issue(self, issue_key: str) -> None:
        self._client.delete(f"/issue/{issue_key}")

    def transition_issue(self, issue_key: str, status: str) -> None:
        """Move `issue_key` through its workflow to the transition matching `status`."""
        data = self._client.get(f"/issue/{issue_key}/transitions")
        transitions = (data or {}).get("transitions", [])

        match = next(
            (
                t
                for t in transitions
                if t.get("name", "").lower() == status.lower()
                or (t.get("to") or {}).get("name", "").lower() == status.lower()
            ),
            None,
        )
        if match is None:
            available = ", ".join(t.get("name", "") for t in transitions) or "none"
            raise ValidationError(
                f"No transition to status '{status}' is available for issue {issue_key}.",
                details=f"Available transitions: {available}",
            )

        self._client.post(
            f"/issue/{issue_key}/transitions", json={"transition": {"id": match["id"]}}
        )
