"""Maps release operations onto Jira Cloud's project version REST endpoints."""

from __future__ import annotations

from datetime import date

from jira_cli.client.exceptions import JiraCliError, ReleaseCreationError, ValidationError
from jira_cli.client.jira_client import JiraClient
from jira_cli.models.release import (
    CurrentRelease,
    FinalizeReleasePlan,
    NextReleasePlan,
    RenameBasePlan,
    Release,
)
from jira_cli.versioning import patch

_NO_VALID_RELEASE_DETAILS = "Expected format:\nMAJOR.MINOR.PATCH\n\nExample:\n25.10.3"


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

    def move_release(self, version_id: str, after_id: str) -> None:
        """Reposition `version_id` to appear immediately after `after_id` in the project."""
        target = self.get_release(after_id)
        self._client.post(f"/version/{version_id}/move", json={"after": target.self_url})

    def rename_versions_by_token(
        self, project: str, search: str, token: str | None = None
    ) -> list[Release]:
        """Strip `token` (default: `search`) out of the name of every release in
        `project` whose name contains `search`. Returns the releases that changed."""
        strip_token = search if token is None else token
        updated: list[Release] = []
        for release in self.list_releases(project):
            if search not in release.name:
                continue
            new_name = " ".join(release.name.replace(strip_token, "").split()).strip(" -")
            if new_name != release.name:
                updated.append(self.update_release(release.id, name=new_name))
        return updated

    def _candidate_version(self, release: Release) -> str | None:
        """The release's plain version: its description if that's a bare valid
        version, else the leading version-shaped token in its name."""
        if release.description and patch.is_valid_patch_version(release.description.strip()):
            return release.description.strip()
        return patch.extract_version_prefix(release.name)

    def _find_current_patch_release(self, project: str) -> tuple[Release, str] | None:
        """Non-archived release with the highest (major, minor, patch) candidate version."""
        candidates: list[tuple[Release, str]] = []
        for release in self.list_releases(project):
            if release.archived:
                continue
            version = self._candidate_version(release)
            if version is not None:
                candidates.append((release, version))
        if not candidates:
            return None
        return max(candidates, key=lambda pair: patch.parse_patch_version(pair[1]))

    def _find_release_by_version(self, project: str, version: str) -> Release | None:
        """First non-archived release whose candidate version equals `version`."""
        for release in self.list_releases(project):
            if release.archived:
                continue
            if self._candidate_version(release) == version:
                return release
        return None

    def _find_release_by_label(self, project: str, label: str) -> Release | None:
        """Among non-archived releases whose name contains `label`, the one with
        the highest candidate version (deterministic if more than one matches)."""
        matches: list[Release] = [
            r for r in self.list_releases(project) if not r.archived and label in r.name
        ]
        if not matches:
            return None

        def sort_key(release: Release) -> tuple[int, int, int]:
            version = self._candidate_version(release)
            return patch.parse_patch_version(version) if version else (-1, -1, -1)

        return max(matches, key=sort_key)

    def get_current_release(self, project: str) -> CurrentRelease | None:
        """Return the current release and its parsed plain version, or None."""
        found = self._find_current_patch_release(project)
        if found is None:
            return None
        release, version = found
        return CurrentRelease(release=release, version=version)

    def plan_next_release(self, project: str, create: bool) -> NextReleasePlan:
        """Calculate the next patch release from the project's current one.

        If no current release is found, bootstraps `YY.MM.1` from today's date.
        If `create` is True and the release does not already exist, it is created
        in Jira, moved after the previous release, and the previous release is
        renamed to "<version> - in Deployment".

        The existence check re-queries Jira separately (rather than reusing the
        initial fetch) so a release created by a concurrent pipeline run in the
        meantime is still detected before we attempt to create a duplicate.
        """
        today = date.today()
        current = self._find_current_patch_release(project)

        if current is None:
            previous_release, previous_version = None, None
            next_version = patch.bootstrap_patch_version(today)
        else:
            previous_release, previous_version = current
            next_version = patch.next_patch_version(previous_version)

        branch_name = f"{next_version} - Release Branch"
        release_date_iso = today.isoformat()
        previous_release_id = previous_release.id if previous_release else None

        existing = self._find_release_by_version(project, next_version)
        if existing is not None:
            return NextReleasePlan(
                project=project,
                previous_release=previous_version,
                previous_release_id=previous_release_id,
                next_release=next_version,
                branch_name=branch_name,
                release_date=release_date_iso,
                release_id=existing.id,
                created=False,
                existing=True,
                moved=False,
                renamed_previous=False,
            )

        if not create:
            return NextReleasePlan(
                project=project,
                previous_release=previous_version,
                previous_release_id=previous_release_id,
                next_release=next_version,
                branch_name=branch_name,
                release_date=release_date_iso,
                release_id=None,
                created=False,
                existing=False,
                moved=False,
                renamed_previous=False,
            )

        try:
            created_release = self.create_release(
                project=project,
                name=branch_name,
                description=next_version,
                start_date=release_date_iso,
                release_date=release_date_iso,
            )
        except JiraCliError:
            raise
        except Exception as exc:  # noqa: BLE001 - wrap unexpected failures as exit code 8
            raise ReleaseCreationError(f"Failed to create release {branch_name}.") from exc

        moved = False
        renamed_previous = False
        if previous_release is not None:
            self.move_release(created_release.id, previous_release.id)
            moved = True
            self.update_release(previous_release.id, name=f"{previous_version} - in Deployment")
            renamed_previous = True

        return NextReleasePlan(
            project=project,
            previous_release=previous_version,
            previous_release_id=previous_release_id,
            next_release=next_version,
            branch_name=branch_name,
            release_date=release_date_iso,
            release_id=created_release.id,
            created=True,
            existing=False,
            moved=moved,
            renamed_previous=renamed_previous,
        )

    def finalize_release(
        self,
        project: str,
        to_label: str,
        from_label: str = "in Deployment",
        strip_token: str | None = None,
        create: bool = True,
    ) -> FinalizeReleasePlan:
        """Rename the release currently carrying `from_label` to carry `to_label`
        instead, and mark it released. If `strip_token` is given, it is first
        stripped from any other release name that still carries it, so only the
        newly-finalized release keeps that label."""
        release = self._find_release_by_label(project, from_label)
        if release is None:
            return FinalizeReleasePlan(
                project=project,
                found=False,
                release_id=None,
                previous_name=None,
                new_name=None,
                stripped_release_ids=[],
                released=False,
            )

        new_name = release.name.replace(from_label, to_label, 1)

        if not create:
            return FinalizeReleasePlan(
                project=project,
                found=True,
                release_id=release.id,
                previous_name=release.name,
                new_name=new_name,
                stripped_release_ids=[],
                released=False,
            )

        stripped: list[Release] = []
        if strip_token is not None:
            stripped = self.rename_versions_by_token(project, strip_token)

        self.update_release(release.id, name=new_name)
        self.update_release(release.id, released=True)

        return FinalizeReleasePlan(
            project=project,
            found=True,
            release_id=release.id,
            previous_name=release.name,
            new_name=new_name,
            stripped_release_ids=[r.id for r in stripped],
            released=True,
        )

    def rename_base_release(self, project: str, version: str, create: bool = True) -> RenameBasePlan:
        """Reset the release matching `version` back to its plain, unsuffixed name."""
        release = self._find_release_by_version(project, version)
        if release is None:
            raise ValidationError(
                f"No release found matching version {version}.", details=_NO_VALID_RELEASE_DETAILS
            )

        if not create:
            return RenameBasePlan(
                project=project,
                version=version,
                release_id=release.id,
                previous_name=release.name,
                new_name=version,
            )

        self.update_release(release.id, name=version)

        return RenameBasePlan(
            project=project,
            version=version,
            release_id=release.id,
            previous_name=release.name,
            new_name=version,
        )
