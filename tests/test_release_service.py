"""Unit tests for ReleaseService's CalVer-driven current/next release logic."""

from __future__ import annotations

from typing import Any

import pytest

from jira_cli.client.exceptions import ValidationError
from jira_cli.services.release_service import ReleaseService


class FakeJiraClient:
    """Minimal stand-in for JiraClient, backed by an in-memory list of versions."""

    def __init__(
        self,
        versions: list[dict[str, Any]],
        on_get: Any = None,
    ) -> None:
        self._versions = versions
        self._next_id = max((int(v["id"]) for v in versions), default=0) + 1
        self._get_count = 0
        self._on_get = on_get

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        assert path.endswith("/versions")
        self._get_count += 1
        if self._on_get is not None:
            self._on_get(self._get_count, self._versions)
        return list(self._versions)

    def post(self, path: str, json: dict[str, Any] | None = None, headers: Any = None) -> Any:
        assert json is not None
        record = {
            "id": str(self._next_id),
            "name": json["name"],
            "projectId": None,
            "released": json.get("released", False),
            "archived": False,
            "startDate": json.get("startDate"),
            "releaseDate": json.get("releaseDate"),
        }
        self._versions.append(record)
        self._next_id += 1
        return record


def make_version(id_: str, name: str, released: bool = False) -> dict[str, Any]:
    return {"id": id_, "name": name, "projectId": "1", "released": released, "archived": False}


def test_get_current_release_picks_latest_valid_calver() -> None:
    client = FakeJiraClient(
        [
            make_version("1", "1.0.0"),
            make_version("2", "26.06.30"),
            make_version("3", "26.07.31"),
            make_version("4", "release-test"),
        ]
    )
    service = ReleaseService(client)

    current = service.get_current_release("PROJ")

    assert current is not None
    assert current.name == "26.07.31"


def test_get_current_release_returns_none_when_no_valid_calver_release() -> None:
    client = FakeJiraClient([make_version("1", "1.0.0"), make_version("2", "release-test")])
    service = ReleaseService(client)

    assert service.get_current_release("PROJ") is None


def test_plan_next_release_creates_when_missing() -> None:
    client = FakeJiraClient([make_version("1", "26.07.31")])
    service = ReleaseService(client)

    plan = service.plan_next_release("PROJ", create=True)

    assert plan.previous_release == "26.07.31"
    assert plan.next_release == "26.08.31"
    assert plan.created is True
    assert plan.existing is False
    assert plan.release_id == "2"


def test_plan_next_release_detects_duplicate_created_concurrently() -> None:
    """A concurrent pipeline run may create the next release between our two Jira reads."""

    def inject_concurrent_release(call_count: int, versions: list[dict[str, Any]]) -> None:
        if call_count == 2:
            versions.append(make_version("2", "26.08.31"))

    client = FakeJiraClient([make_version("1", "26.07.31")], on_get=inject_concurrent_release)
    service = ReleaseService(client)

    plan = service.plan_next_release("PROJ", create=True)

    assert plan.next_release == "26.08.31"
    assert plan.created is False
    assert plan.existing is True
    assert plan.release_id == "2"
    assert len(client._versions) == 2  # no duplicate was created


def test_plan_next_release_dry_run_does_not_create() -> None:
    client = FakeJiraClient([make_version("1", "26.07.31")])
    service = ReleaseService(client)

    plan = service.plan_next_release("PROJ", create=False)

    assert plan.next_release == "26.08.31"
    assert plan.created is False
    assert plan.existing is False
    assert plan.release_id is None
    assert len(client._versions) == 1  # dry run: nothing created


def test_plan_next_release_raises_when_no_valid_current_release() -> None:
    client = FakeJiraClient([make_version("1", "1.0.0")])
    service = ReleaseService(client)

    with pytest.raises(ValidationError):
        service.plan_next_release("PROJ", create=True)


def test_plan_next_release_handles_year_rollover() -> None:
    client = FakeJiraClient([make_version("1", "26.12.31")])
    service = ReleaseService(client)

    plan = service.plan_next_release("PROJ", create=True)

    assert plan.next_release == "27.01.31"
