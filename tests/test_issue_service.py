"""Unit tests for IssueService's comment, assign, and transition operations."""

from __future__ import annotations

from typing import Any

import pytest

from jira_cli.client.exceptions import ValidationError
from jira_cli.services.issue_service import IssueService


class FakeJiraClient:
    def __init__(
        self,
        transitions: list[dict[str, Any]] | None = None,
        issues: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self.transitions = transitions or []
        self.issues = issues or {}
        self.puts: list[tuple[str, dict[str, Any] | None]] = []
        self.posts: list[tuple[str, dict[str, Any] | None]] = []
        self.deletes: list[str] = []
        self._next_id = 1000

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        if path.endswith("/transitions"):
            return {"transitions": self.transitions}
        key = path.rsplit("/", 1)[-1]
        return self.issues[key]

    def put(self, path: str, json: dict[str, Any] | None = None) -> Any:
        self.puts.append((path, json))
        return None

    def post(self, path: str, json: dict[str, Any] | None = None, headers: Any = None) -> Any:
        self.posts.append((path, json))
        if path == "/issue":
            fields = json["fields"]
            key = f"PROJ-{self._next_id}"
            self._next_id += 1
            self.issues[key] = {
                "key": key,
                "fields": {
                    "summary": fields.get("summary", ""),
                    "status": {"name": "Open"},
                    "issuetype": fields.get("issuetype", {}),
                    "project": fields.get("project", {}),
                    "assignee": None,
                },
            }
            return {"id": str(self._next_id), "key": key, "self": "https://example/rest/api/3/issue/1"}
        return None

    def delete(self, path: str) -> None:
        self.deletes.append(path)


def test_assign_issue_puts_account_id() -> None:
    client = FakeJiraClient()
    service = IssueService(client)

    service.assign_issue("PROJ-123", "abc-account-id")

    assert client.puts == [("/issue/PROJ-123/assignee", {"accountId": "abc-account-id"})]


def test_transition_issue_matches_by_transition_name() -> None:
    client = FakeJiraClient(
        transitions=[
            {"id": "11", "name": "In Progress", "to": {"name": "In Progress"}},
            {"id": "31", "name": "Done", "to": {"name": "Done"}},
        ]
    )
    service = IssueService(client)

    service.transition_issue("PROJ-123", "Done")

    assert client.posts == [
        ("/issue/PROJ-123/transitions", {"transition": {"id": "31"}})
    ]


def test_transition_issue_matches_case_insensitively() -> None:
    client = FakeJiraClient(transitions=[{"id": "31", "name": "Done", "to": {"name": "Done"}}])
    service = IssueService(client)

    service.transition_issue("PROJ-123", "done")

    assert client.posts == [
        ("/issue/PROJ-123/transitions", {"transition": {"id": "31"}})
    ]


def test_transition_issue_raises_when_status_unavailable() -> None:
    client = FakeJiraClient(transitions=[{"id": "11", "name": "In Progress", "to": {"name": "In Progress"}}])
    service = IssueService(client)

    with pytest.raises(ValidationError):
        service.transition_issue("PROJ-123", "Done")

    assert client.posts == []


def test_create_issue_posts_service_factory_field_and_reporter() -> None:
    client = FakeJiraClient()
    service = IssueService(client)

    issue = service.create_issue(
        "PROJ", "Deploy release", "Task", "Platform", "author-account-id"
    )

    assert client.posts[0][0] == "/issue"
    body = client.posts[0][1]
    assert body["fields"]["project"] == {"key": "PROJ"}
    assert body["fields"]["summary"] == "Deploy release"
    assert body["fields"]["issuetype"] == {"name": "Task"}
    assert body["fields"]["customfield_10829"] == {
        "value": "Improvements",
        "child": {"value": "Platform"},
    }
    assert body["fields"]["reporter"] == {"id": "author-account-id"}
    assert "description" not in body["fields"]
    assert issue.summary == "Deploy release"


def test_create_issue_includes_description_when_given() -> None:
    client = FakeJiraClient()
    service = IssueService(client)

    service.create_issue(
        "PROJ", "Deploy release", "Task", "Platform", "author-account-id",
        description="Some details",
    )

    body = client.posts[0][1]
    assert body["fields"]["description"]["content"][0]["content"][0]["text"] == "Some details"


def test_delete_issue_sends_delete_request() -> None:
    client = FakeJiraClient()
    service = IssueService(client)

    service.delete_issue("PROJ-123")

    assert client.deletes == ["/issue/PROJ-123"]
