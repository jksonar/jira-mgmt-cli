"""Unit tests for ReleaseService's patch-counter release lifecycle."""

from __future__ import annotations

from datetime import date
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
        self.moves: list[tuple[str, dict[str, Any]]] = []

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        if path.endswith("/versions"):
            self._get_count += 1
            if self._on_get is not None:
                self._on_get(self._get_count, self._versions)
            return list(self._versions)

        version_id = path.rsplit("/", 1)[-1]
        for version in self._versions:
            if version["id"] == version_id:
                return version
        raise AssertionError(f"version {version_id} not found")

    def post(self, path: str, json: dict[str, Any] | None = None, headers: Any = None) -> Any:
        assert json is not None
        if path.endswith("/move"):
            version_id = path.split("/")[-2]
            self.moves.append((version_id, json))
            return None

        record = {
            "id": str(self._next_id),
            "name": json["name"],
            "description": json.get("description"),
            "projectId": None,
            "released": json.get("released", False),
            "archived": False,
            "startDate": json.get("startDate"),
            "releaseDate": json.get("releaseDate"),
            "self": f"https://example.atlassian.net/rest/api/3/version/{self._next_id}",
        }
        self._versions.append(record)
        self._next_id += 1
        return record

    def put(self, path: str, json: dict[str, Any] | None = None) -> Any:
        assert json is not None
        version_id = path.rsplit("/", 1)[-1]
        for version in self._versions:
            if version["id"] == version_id:
                version.update(
                    {
                        "name": json.get("name", version["name"]),
                        "description": json.get("description", version.get("description")),
                        "released": json.get("released", version.get("released", False)),
                        "archived": json.get("archived", version.get("archived", False)),
                        "startDate": json.get("startDate", version.get("startDate")),
                        "releaseDate": json.get("releaseDate", version.get("releaseDate")),
                    }
                )
                return version
        raise AssertionError(f"version {version_id} not found")


def make_version(
    id_: str,
    name: str,
    description: str | None = None,
    released: bool = False,
    archived: bool = False,
) -> dict[str, Any]:
    return {
        "id": id_,
        "name": name,
        "description": description,
        "projectId": "1",
        "released": released,
        "archived": archived,
        "self": f"https://example.atlassian.net/rest/api/3/version/{id_}",
    }


# --- get_current_release -----------------------------------------------------


def test_get_current_release_resolves_from_description() -> None:
    client = FakeJiraClient([make_version("1", "25.10.2 - Release Branch", description="25.10.2")])
    service = ReleaseService(client)

    current = service.get_current_release("PROJ")

    assert current is not None
    assert current.version == "25.10.2"
    assert current.release.id == "1"


def test_get_current_release_resolves_from_suffixed_name_without_description() -> None:
    client = FakeJiraClient([make_version("1", "25.10.2 - in Deployment")])
    service = ReleaseService(client)

    current = service.get_current_release("PROJ")

    assert current is not None
    assert current.version == "25.10.2"


def test_get_current_release_picks_highest_version() -> None:
    client = FakeJiraClient(
        [
            make_version("1", "25.10.9 - in Deployment", description="25.10.9"),
            make_version("2", "25.10.10 - Release Branch", description="25.10.10"),
        ]
    )
    service = ReleaseService(client)

    current = service.get_current_release("PROJ")

    assert current is not None
    assert current.version == "25.10.10"  # numeric, not lexicographic, comparison


def test_get_current_release_returns_none_when_nothing_matches() -> None:
    client = FakeJiraClient([make_version("1", "release-test")])
    service = ReleaseService(client)

    assert service.get_current_release("PROJ") is None


def test_get_current_release_ignores_archived() -> None:
    client = FakeJiraClient(
        [make_version("1", "25.10.2", description="25.10.2", archived=True)]
    )
    service = ReleaseService(client)

    assert service.get_current_release("PROJ") is None


# --- plan_next_release ---------------------------------------------------------


def test_plan_next_release_bumps_patch_from_description() -> None:
    client = FakeJiraClient([make_version("1", "25.10.2 - Release Branch", description="25.10.2")])
    service = ReleaseService(client)

    plan = service.plan_next_release("PROJ", create=True)

    assert plan.previous_release == "25.10.2"
    assert plan.next_release == "25.10.3"
    assert plan.branch_name == "25.10.3 - Release Branch"
    assert plan.created is True
    assert plan.existing is False
    assert plan.release_date == date.today().isoformat()


def test_plan_next_release_bootstraps_when_no_current_release() -> None:
    client = FakeJiraClient([])
    service = ReleaseService(client)

    plan = service.plan_next_release("PROJ", create=True)

    today = date.today()
    expected = f"{today.year % 100:02d}.{today.month:02d}.1"
    assert plan.previous_release is None
    assert plan.next_release == expected
    assert plan.created is True
    assert plan.moved is False
    assert plan.renamed_previous is False


def test_plan_next_release_moves_and_renames_previous() -> None:
    client = FakeJiraClient([make_version("1", "25.10.2 - Release Branch", description="25.10.2")])
    service = ReleaseService(client)

    plan = service.plan_next_release("PROJ", create=True)

    assert plan.moved is True
    assert plan.renamed_previous is True
    assert len(client.moves) == 1
    moved_id, move_body = client.moves[0]
    assert moved_id == plan.release_id
    assert move_body == {"after": "https://example.atlassian.net/rest/api/3/version/1"}

    previous = next(v for v in client._versions if v["id"] == "1")
    assert previous["name"] == "25.10.2 - in Deployment"


def test_plan_next_release_detects_duplicate_created_concurrently() -> None:
    def inject_concurrent_release(call_count: int, versions: list[dict[str, Any]]) -> None:
        if call_count == 2:
            versions.append(make_version("2", "25.10.3 - Release Branch", description="25.10.3"))

    client = FakeJiraClient(
        [make_version("1", "25.10.2 - Release Branch", description="25.10.2")],
        on_get=inject_concurrent_release,
    )
    service = ReleaseService(client)

    plan = service.plan_next_release("PROJ", create=True)

    assert plan.next_release == "25.10.3"
    assert plan.created is False
    assert plan.existing is True
    assert plan.moved is False
    assert plan.renamed_previous is False
    assert plan.release_id == "2"
    assert len(client._versions) == 2  # no duplicate was created


def test_plan_next_release_dry_run_does_not_mutate() -> None:
    client = FakeJiraClient([make_version("1", "25.10.2 - Release Branch", description="25.10.2")])
    service = ReleaseService(client)

    plan = service.plan_next_release("PROJ", create=False)

    assert plan.next_release == "25.10.3"
    assert plan.created is False
    assert plan.existing is False
    assert plan.release_id is None
    assert len(client._versions) == 1
    assert client.moves == []


# --- move_release --------------------------------------------------------------


def test_move_release_posts_target_self_url() -> None:
    client = FakeJiraClient(
        [
            make_version("1", "25.10.2 - Release Branch"),
            make_version("2", "25.10.3 - Release Branch"),
        ]
    )
    service = ReleaseService(client)

    service.move_release("2", "1")

    assert client.moves == [
        ("2", {"after": "https://example.atlassian.net/rest/api/3/version/1"})
    ]


# --- rename_versions_by_token ----------------------------------------------------


def test_rename_versions_by_token_only_touches_matching_names() -> None:
    client = FakeJiraClient(
        [
            make_version("1", "25.10.1 - on DEV"),
            make_version("2", "25.10.2 - Release Branch"),
        ]
    )
    service = ReleaseService(client)

    updated = service.rename_versions_by_token("PROJ", "DEV")

    assert [r.id for r in updated] == ["1"]
    assert updated[0].name == "25.10.1 - on"
    unchanged = next(v for v in client._versions if v["id"] == "2")
    assert unchanged["name"] == "25.10.2 - Release Branch"


# --- finalize_release -----------------------------------------------------------


def test_finalize_release_renames_and_marks_released() -> None:
    client = FakeJiraClient([make_version("1", "25.10.2 - in Deployment", description="25.10.2")])
    service = ReleaseService(client)

    plan = service.finalize_release("PROJ", to_label="on DEV")

    assert plan.found is True
    assert plan.new_name == "25.10.2 - on DEV"
    assert plan.released is True
    updated = next(v for v in client._versions if v["id"] == "1")
    assert updated["name"] == "25.10.2 - on DEV"
    assert updated["released"] is True


def test_finalize_release_strips_token_from_other_releases_first() -> None:
    client = FakeJiraClient(
        [
            make_version("1", "25.10.1 - on DEV", description="25.10.1"),
            make_version("2", "25.10.2 - in Deployment", description="25.10.2"),
        ]
    )
    service = ReleaseService(client)

    plan = service.finalize_release("PROJ", to_label="on DEV", strip_token="DEV")

    assert plan.stripped_release_ids == ["1"]
    stripped = next(v for v in client._versions if v["id"] == "1")
    assert "DEV" not in stripped["name"]
    finalized = next(v for v in client._versions if v["id"] == "2")
    assert finalized["name"] == "25.10.2 - on DEV"


def test_finalize_release_returns_not_found_when_no_label_match() -> None:
    client = FakeJiraClient([make_version("1", "25.10.2 - Release Branch")])
    service = ReleaseService(client)

    plan = service.finalize_release("PROJ", to_label="on DEV")

    assert plan.found is False
    assert plan.release_id is None


def test_finalize_release_dry_run_does_not_mutate() -> None:
    client = FakeJiraClient([make_version("1", "25.10.2 - in Deployment", description="25.10.2")])
    service = ReleaseService(client)

    plan = service.finalize_release("PROJ", to_label="on DEV", create=False)

    assert plan.found is True
    assert plan.new_name == "25.10.2 - on DEV"
    assert plan.released is False
    unchanged = next(v for v in client._versions if v["id"] == "1")
    assert unchanged["name"] == "25.10.2 - in Deployment"


# --- rename_base_release ---------------------------------------------------------


def test_rename_base_release_resets_name() -> None:
    client = FakeJiraClient([make_version("1", "25.10.1 - on DEV", description="25.10.1")])
    service = ReleaseService(client)

    plan = service.rename_base_release("PROJ", "25.10.1")

    assert plan.release_id == "1"
    assert plan.new_name == "25.10.1"
    updated = next(v for v in client._versions if v["id"] == "1")
    assert updated["name"] == "25.10.1"


def test_rename_base_release_raises_when_not_found() -> None:
    client = FakeJiraClient([make_version("1", "25.10.2 - Release Branch")])
    service = ReleaseService(client)

    with pytest.raises(ValidationError):
        service.rename_base_release("PROJ", "25.10.1")
