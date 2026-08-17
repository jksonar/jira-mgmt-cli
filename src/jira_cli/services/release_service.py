"""Maps release operations onto Jira Cloud's project version REST endpoints."""

from __future__ import annotations

from jira_cli.client.exceptions import JiraCliError, ReleaseCreationError, ValidationError
from jira_cli.client.jira_client import JiraClient
from jira_cli.models.release import NextReleasePlan, Release
from jira_cli.versioning.calver import is_valid_calver, latest_calver, next_calver

_NO_VALID_RELEASE_DETAILS = "Expected format:\nYY.MM.DD\n\nExample:\n26.08.31"


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

    def get_current_release(self, project: str) -> Release | None:
        """Return the newest release whose name is a valid CalVer (YY.MM.DD) version, or None."""
        return self._latest_calver_release(self.list_releases(project))

    def plan_next_release(self, project: str, create: bool) -> NextReleasePlan:
        """Calculate the next CalVer release from the project's current one.

        If `create` is True and the release does not already exist, it is created in Jira.
        Raises ValidationError if no valid CalVer release exists yet to calculate from.

        The existence check re-queries Jira separately (rather than reusing the initial
        fetch) so a release created by a concurrent pipeline run in the meantime is still
        detected before we attempt to create a duplicate.
        """
        current = self._latest_calver_release(self.list_releases(project))
        if current is None:
            raise ValidationError(
                "No valid CalVer release found.", details=_NO_VALID_RELEASE_DETAILS
            )

        next_version = next_calver(current.name)
        existing = next(
            (r for r in self.list_releases(project) if r.name == next_version), None
        )

        if existing is not None:
            return NextReleasePlan(
                project=project,
                previous_release=current.name,
                next_release=next_version,
                release_id=existing.id,
                created=False,
                existing=True,
            )

        if not create:
            return NextReleasePlan(
                project=project,
                previous_release=current.name,
                next_release=next_version,
                release_id=None,
                created=False,
                existing=False,
            )

        try:
            created_release = self.create_release(project=project, name=next_version)
        except JiraCliError:
            raise
        except Exception as exc:  # noqa: BLE001 - wrap unexpected failures as exit code 8
            raise ReleaseCreationError(f"Failed to create release {next_version}.") from exc

        return NextReleasePlan(
            project=project,
            previous_release=current.name,
            next_release=next_version,
            release_id=created_release.id,
            created=True,
            existing=False,
        )

    @staticmethod
    def _latest_calver_release(releases: list[Release]) -> Release | None:
        by_name = {r.name: r for r in releases if is_valid_calver(r.name)}
        if not by_name:
            return None
        latest_name = latest_calver(list(by_name.keys()))
        return by_name[latest_name] if latest_name is not None else None
