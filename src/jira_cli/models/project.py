"""Project model: a Jira project."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Project:
    key: str
    name: str
    id: str | None = None
    project_type: str | None = None
    lead: str | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Project":
        lead = data.get("lead") or {}
        return cls(
            key=data.get("key", ""),
            name=data.get("name", ""),
            id=str(data["id"]) if data.get("id") is not None else None,
            project_type=data.get("projectTypeKey"),
            lead=lead.get("displayName"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "id": self.id,
            "project_type": self.project_type,
            "lead": self.lead,
        }
