"""Unit tests for IssueService's comment, assign, and transition operations."""

from __future__ import annotations

from typing import Any

import pytest

from jira_cli.client.exceptions import ValidationError
from jira_cli.services.issue_service import IssueService


class FakeJiraClient:
    def __init__(self, transitions: list[dict[str, Any]] | None = None) -> None:
        self.transitions = transitions or []
        self.puts: list[tuple[str, dict[str, Any] | None]] = []
        self.posts: list[tuple[str, dict[str, Any] | None]] = []

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        assert path.endswith("/transitions")
        return {"transitions": self.transitions}

    def put(self, path: str, json: dict[str, Any] | None = None) -> Any:
        self.puts.append((path, json))
        return None

    def post(self, path: str, json: dict[str, Any] | None = None, headers: Any = None) -> Any:
        self.posts.append((path, json))
        return None


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
