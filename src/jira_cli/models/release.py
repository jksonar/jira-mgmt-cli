"""Release model: a Jira project version."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Release:
    id: str
    name: str
    description: str | None = None
    project_id: str | None = None
    released: bool = False
    archived: bool = False
    start_date: str | None = None
    release_date: str | None = None
    self_url: str | None = None
    """Jira's `self` REST URL for this version, needed to build `move` request bodies."""

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Release":
        return cls(
            id=str(data.get("id")),
            name=data.get("name", ""),
            description=data.get("description"),
            project_id=(
                str(data["projectId"]) if data.get("projectId") is not None else None
            ),
            released=bool(data.get("released", False)),
            archived=bool(data.get("archived", False)),
            start_date=data.get("startDate"),
            release_date=data.get("releaseDate"),
            self_url=data.get("self"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "project_id": self.project_id,
            "released": self.released,
            "archived": self.archived,
            "start_date": self.start_date,
            "release_date": self.release_date,
        }


@dataclass(frozen=True)
class CurrentRelease:
    """The current release, plus the plain MAJOR.MINOR.PATCH version parsed from it."""

    release: Release
    version: str


@dataclass(frozen=True)
class NextReleasePlan:
    """Result of calculating (and optionally creating) the next patch release."""

    project: str
    previous_release: str | None
    previous_release_id: str | None
    next_release: str
    branch_name: str
    release_date: str
    release_id: str | None
    created: bool
    existing: bool
    moved: bool
    renamed_previous: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "previous_release": self.previous_release,
            "previous_release_id": self.previous_release_id,
            "next_release": self.next_release,
            "branch_name": self.branch_name,
            "release_date": self.release_date,
            "release_id": self.release_id,
            "created": self.created,
            "existing": self.existing,
            "moved": self.moved,
            "renamed_previous": self.renamed_previous,
        }


@dataclass(frozen=True)
class FinalizeReleasePlan:
    """Result of finalizing the release currently carrying `from_label`."""

    project: str
    found: bool
    release_id: str | None
    previous_name: str | None
    new_name: str | None
    stripped_release_ids: list[str]
    released: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "found": self.found,
            "release_id": self.release_id,
            "previous_name": self.previous_name,
            "new_name": self.new_name,
            "stripped_release_ids": self.stripped_release_ids,
            "released": self.released,
        }


@dataclass(frozen=True)
class RenameBasePlan:
    """Result of resetting a release's name back to its plain version."""

    project: str
    version: str
    release_id: str
    previous_name: str
    new_name: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "version": self.version,
            "release_id": self.release_id,
            "previous_name": self.previous_name,
            "new_name": self.new_name,
        }
