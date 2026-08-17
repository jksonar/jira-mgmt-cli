"""Maps project operations onto Jira Cloud's project REST endpoints."""

from __future__ import annotations

from jira_cli.client.jira_client import JiraClient
from jira_cli.models.project import Project


class ProjectService:
    def __init__(self, client: JiraClient) -> None:
        self._client = client

    def list_projects(self) -> list[Project]:
        data = self._client.get("/project/search", params={"expand": "lead"})
        values = (data or {}).get("values", [])
        return [Project.from_api(p) for p in values]

    def get_project(self, project: str) -> Project:
        data = self._client.get(f"/project/{project}")
        return Project.from_api(data)
