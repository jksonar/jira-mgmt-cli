"""Thin HTTP client wrapping httpx for Jira Cloud REST API v3 calls."""

from __future__ import annotations

from typing import Any

import httpx

from jira_cli.client.authentication import build_basic_auth
from jira_cli.client.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NetworkError,
    NotFoundError,
    ValidationError,
)
from jira_cli.config.settings import Settings
from jira_cli.utils.logger import get_logger

JIRA_API_VERSION = "3"

_logger = get_logger("client")


def _extract_error_message(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.text or f"HTTP {response.status_code}"

    messages = body.get("errorMessages") or []
    errors = body.get("errors") or {}
    parts = list(messages) + [f"{field}: {msg}" for field, msg in errors.items()]
    return "; ".join(parts) if parts else f"HTTP {response.status_code}"


class JiraClient:
    def __init__(
        self, settings: Settings, timeout: float = 30.0, verify_ssl: bool = True
    ) -> None:
        self._http = httpx.Client(
            base_url=settings.jira_url,
            auth=build_basic_auth(settings),
            timeout=timeout,
            verify=verify_ssl,
            headers={"Accept": "application/json"},
        )

    def __enter__(self) -> "JiraClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()

    def _build_path(self, path: str) -> str:
        return f"/rest/api/{JIRA_API_VERSION}/{path.lstrip('/')}"

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        full_path = self._build_path(path)
        _logger.debug("Request: %s %s", method, full_path)

        try:
            response = self._http.request(method, full_path, **kwargs)
        except httpx.RequestError as exc:
            raise NetworkError(f"Network error contacting Jira: {exc}") from exc

        _logger.debug("Response: %s", response.status_code)

        if response.status_code == 401:
            raise AuthenticationError("Jira authentication failed.")
        if response.status_code == 403:
            raise AuthorizationError(_extract_error_message(response))
        if response.status_code == 404:
            raise NotFoundError(_extract_error_message(response))
        if response.status_code in (400, 422):
            raise ValidationError(_extract_error_message(response))
        if response.status_code >= 300:
            raise NetworkError(
                f"Unexpected Jira response: {_extract_error_message(response)}"
            )

        if not response.content:
            return None
        return response.json()

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._request("GET", path, params=params)

    def post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        files: Any = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        kwargs: dict[str, Any] = {"headers": headers}
        if files is not None:
            # Multipart upload: `json` and `files` are mutually exclusive in httpx.
            kwargs["files"] = files
        else:
            kwargs["json"] = json
        return self._request("POST", path, **kwargs)

    def put(self, path: str, json: dict[str, Any] | None = None) -> Any:
        return self._request("PUT", path, json=json)

    def delete(self, path: str) -> None:
        self._request("DELETE", path)
