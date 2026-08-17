"""Unit tests for ReleaseService's `--date` override on `plan_next_release`."""

from __future__ import annotations

from typing import Any

import pytest

from jira_cli.services.release_service import ReleaseService


class FakeJiraClient:
    """Minimal stand-in for JiraClient, backed by an in-memory list of versions."""

    def __init__(self, versions: list[dict[str, Any]]) -> None:
        self._versions = versions
        self._next_id = max((int(v["id"]) for v in versions), default=0) + 1

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        assert path.endswith("/versions")
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


@pytest.mark.parametrize(
    ("date_override", "expected_version"),
    [
        ("2026-08-20", "26.08.20"),
        ("2026-08-25", "26.08.25"),
        ("2026-09-15", "26.09.15"),
        ("2027-01-31", "27.01.31"),
    ],
)
def test_plan_next_release_uses_explicit_date_verbatim(
    date_override: str, expected_version: str
) -> None:
    client = FakeJiraClient([make_version("1", "26.07.31")])
    service = ReleaseService(client)

    plan = service.plan_next_release("PROJ", create=True, date_override=date_override)

    assert plan.next_release == expected_version
    assert plan.release_date == date_override
    assert plan.requested_date == date_override
    assert plan.created is True


def test_plan_next_release_explicit_date_is_never_pushed_to_month_end() -> None:
    """Rule 3: an explicit --date must never be replaced by the last day of the month."""
    client = FakeJiraClient([make_version("1", "26.07.31")])
    service = ReleaseService(client)

    plan = service.plan_next_release("PROJ", create=True, date_override="2026-08-15")

    assert plan.next_release == "26.08.15"
    assert plan.next_release != "26.08.31"


def test_plan_next_release_explicit_date_detects_duplicate() -> None:
    client = FakeJiraClient([make_version("1", "26.07.31"), make_version("2", "26.08.20")])
    service = ReleaseService(client)

    plan = service.plan_next_release("PROJ", create=True, date_override="2026-08-20")

    assert plan.existing is True
    assert plan.created is False
    assert plan.release_id == "2"


def test_plan_next_release_explicit_date_sets_jira_release_date() -> None:
    client = FakeJiraClient([make_version("1", "26.07.31")])
    service = ReleaseService(client)

    service.plan_next_release("PROJ", create=True, date_override="2026-08-20")

    created = client._versions[-1]
    assert created["releaseDate"] == "2026-08-20"


def test_plan_next_release_without_date_sets_computed_release_date() -> None:
    client = FakeJiraClient([make_version("1", "26.07.31")])
    service = ReleaseService(client)

    plan = service.plan_next_release("PROJ", create=True)

    assert plan.release_date == "2026-08-31"
    assert plan.requested_date is None
    assert client._versions[-1]["releaseDate"] == "2026-08-31"
