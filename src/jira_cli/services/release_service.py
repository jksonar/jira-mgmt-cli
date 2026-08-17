"""Maps release operations onto Jira Cloud's project version REST endpoints."""

from __future__ import annotations

from jira_cli.client.exceptions import ValidationError
from jira_cli.client.jira_client import JiraClient
from jira_cli.models.release import Release


class ReleaseService:
    def __init__(self, client: JiraClient) -> None:
        self._client = client

    def list_releases(self, project: str) -> list[Release]:
        versions = self._client.get(f"/project/{project}/versions")
        return [Release.from_api(v) for v in versions or []]

    def get_release(self, version_id: str) -> Release:
        data = self._client.get(f"/version/{version_id}")
        return Release.from_api(data)

    def create_release(
        self,
        project: str,
        name: str,
        description: str | None = None,
        start_date: str | None = None,
        release_date: str | None = None,
        released: bool = False,
    ) -> Release:
        body: dict[str, object] = {
            "name": name,
            "project": project,
            "released": released,
        }
        if description is not None:
            body["description"] = description
        if start_date is not None:
            body["startDate"] = start_date
        if release_date is not None:
            body["releaseDate"] = release_date

        data = self._client.post("/version", json=body)
        return Release.from_api(data)

    def update_release(
        self,
        version_id: str,
        name: str | None = None,
        description: str | None = None,
        start_date: str | None = None,
        release_date: str | None = None,
        released: bool | None = None,
    ) -> Release:
        body: dict[str, object] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if start_date is not None:
            body["startDate"] = start_date
        if release_date is not None:
            body["releaseDate"] = release_date
        if released is not None:
            body["released"] = released

        if not body:
            raise ValidationError("No fields provided to update.")

        data = self._client.put(f"/version/{version_id}", json=body)
        return Release.from_api(data)

    def publish_release(self, version_id: str) -> Release:
        data = self._client.put(f"/version/{version_id}", json={"released": True})
        return Release.from_api(data)

    def archive_release(self, version_id: str) -> Release:
        data = self._client.put(f"/version/{version_id}", json={"archived": True})
        return Release.from_api(data)

    def delete_release(self, version_id: str) -> None:
        self._client.delete(f"/version/{version_id}")
