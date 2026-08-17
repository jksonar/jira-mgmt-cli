"""Unit tests for ArtifactService's file validation and attachment upload."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from jira_cli.client.exceptions import ArtifactError
from jira_cli.services.artifact_service import ArtifactService


class FakeJiraClient:
    def __init__(self) -> None:
        self.post_calls: list[dict[str, Any]] = []

    def post(self, path: str, json: Any = None, files: Any = None, headers: Any = None) -> Any:
        self.post_calls.append({"path": path, "files": files, "headers": headers})
        return [
            {"id": "1001", "filename": name, "size": 42, "mimeType": "application/octet-stream"}
            for _, (name, _handle, _mime) in files
        ]


def test_validate_artifact_raises_when_file_missing(tmp_path: Path) -> None:
    service = ArtifactService(FakeJiraClient())
    missing = tmp_path / "does-not-exist.zip"

    with pytest.raises(ArtifactError):
        service.validate_artifact(str(missing))


def test_validate_artifact_raises_when_path_is_a_directory(tmp_path: Path) -> None:
    service = ArtifactService(FakeJiraClient())

    with pytest.raises(ArtifactError):
        service.validate_artifact(str(tmp_path))


def test_validate_artifact_accepts_existing_file(tmp_path: Path) -> None:
    service = ArtifactService(FakeJiraClient())
    file_path = tmp_path / "application.zip"
    file_path.write_bytes(b"binary-content")

    result = service.validate_artifact(str(file_path))

    assert result == file_path


def test_upload_artifact_sends_multipart_with_no_check_header(tmp_path: Path) -> None:
    client = FakeJiraClient()
    service = ArtifactService(client)
    file_path = tmp_path / "application.zip"
    file_path.write_bytes(b"binary-content")

    attachments = service.upload_artifact("PROJ-123", str(file_path))

    assert len(attachments) == 1
    assert attachments[0].filename == "application.zip"
    assert client.post_calls[0]["path"] == "/issue/PROJ-123/attachments"
    assert client.post_calls[0]["headers"] == {"X-Atlassian-Token": "no-check"}


def test_upload_multiple_artifacts_uploads_all_files(tmp_path: Path) -> None:
    client = FakeJiraClient()
    service = ArtifactService(client)
    file_a = tmp_path / "application.zip"
    file_b = tmp_path / "checksum.txt"
    file_a.write_bytes(b"a")
    file_b.write_bytes(b"b")

    attachments = service.upload_multiple_artifacts("PROJ-123", [str(file_a), str(file_b)])

    assert {a.filename for a in attachments} == {"application.zip", "checksum.txt"}


def test_upload_multiple_artifacts_validates_before_opening_any_handle(tmp_path: Path) -> None:
    client = FakeJiraClient()
    service = ArtifactService(client)
    good = tmp_path / "good.zip"
    good.write_bytes(b"a")
    missing = tmp_path / "missing.zip"

    with pytest.raises(ArtifactError):
        service.upload_multiple_artifacts("PROJ-123", [str(good), str(missing)])

    assert client.post_calls == []
