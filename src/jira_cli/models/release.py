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
class NextReleasePlan:
    """Result of calculating (and optionally creating) the next CalVer release for a project."""

    project: str
    previous_release: str | None
    next_release: str
    release_date: str
    release_id: str | None
    created: bool
    existing: bool
    requested_date: str | None = None
    """The `--date` value the caller supplied, or None if it was calculated automatically."""

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "previous_release": self.previous_release,
            "next_release": self.next_release,
            "release_date": self.release_date,
            "release_id": self.release_id,
            "created": self.created,
            "existing": self.existing,
        }
