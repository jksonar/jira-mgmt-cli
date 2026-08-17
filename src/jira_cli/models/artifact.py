"""Artifact model: a file attached to a Jira issue (Jira attachment)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Attachment:
    id: str
    filename: str
    size: int
    mime_type: str | None = None
    created: str | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Attachment":
        return cls(
            id=str(data.get("id")),
            filename=data.get("filename", ""),
            size=int(data.get("size") or 0),
            mime_type=data.get("mimeType"),
            created=data.get("created"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "filename": self.filename,
            "size": self.size,
            "mime_type": self.mime_type,
            "created": self.created,
        }
