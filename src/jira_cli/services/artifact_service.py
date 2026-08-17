"""Maps artifact operations onto Jira Cloud's issue attachment REST endpoints."""

from __future__ import annotations

from pathlib import Path

from jira_cli.client.exceptions import ArtifactError
from jira_cli.client.jira_client import JiraClient
from jira_cli.models.artifact import Attachment

# Jira Cloud rejects attachments above this size; checked locally so failures are fast
# and unambiguous rather than surfacing as an opaque HTTP error mid-upload.
MAX_ARTIFACT_SIZE_BYTES = 200 * 1024 * 1024


class ArtifactService:
    def __init__(self, client: JiraClient) -> None:
        self._client = client

    def validate_artifact(self, file_path: str) -> Path:
        path = Path(file_path)
        if not path.exists():
            raise ArtifactError("Artifact file does not exist:", details=file_path)
        if not path.is_file():
            raise ArtifactError("Artifact path is not a regular file:", details=file_path)

        try:
            handle = path.open("rb")
        except OSError as exc:
            raise ArtifactError("Artifact file is not readable:", details=file_path) from exc
        else:
            handle.close()

        size = path.stat().st_size
        if size > MAX_ARTIFACT_SIZE_BYTES:
            raise ArtifactError(
                "Artifact file exceeds the maximum allowed size.",
                details=f"{file_path} is {size} bytes (limit {MAX_ARTIFACT_SIZE_BYTES} bytes).",
            )
        return path

    def upload_artifact(self, issue_key: str, file_path: str) -> list[Attachment]:
        return self.upload_multiple_artifacts(issue_key, [file_path])

    def upload_multiple_artifacts(self, issue_key: str, file_paths: list[str]) -> list[Attachment]:
        paths = [self.validate_artifact(file_path) for file_path in file_paths]

        handles = [path.open("rb") for path in paths]
        try:
            files = [
                ("file", (path.name, handle, "application/octet-stream"))
                for path, handle in zip(paths, handles)
            ]
            data = self._client.post(
                f"/issue/{issue_key}/attachments",
                files=files,
                headers={"X-Atlassian-Token": "no-check"},
            )
        finally:
            for handle in handles:
                handle.close()

        return [Attachment.from_api(item) for item in data or []]

    def get_attachment_metadata(self, attachment_id: str) -> Attachment:
        data = self._client.get(f"/attachment/{attachment_id}")
        return Attachment.from_api(data)
