"""Issue model: a Jira issue."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Issue:
    key: str
    summary: str
    status: str | None = None
    issue_type: str | None = None
    project_key: str | None = None
    assignee: str | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Issue":
        fields = data.get("fields") or {}
        status = fields.get("status") or {}
        issue_type = fields.get("issuetype") or {}
        project = fields.get("project") or {}
        assignee = fields.get("assignee") or {}
        return cls(
            key=data.get("key", ""),
            summary=fields.get("summary", ""),
            status=status.get("name"),
            issue_type=issue_type.get("name"),
            project_key=project.get("key"),
            assignee=assignee.get("displayName"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "summary": self.summary,
            "status": self.status,
            "issue_type": self.issue_type,
            "project_key": self.project_key,
            "assignee": self.assignee,
        }
