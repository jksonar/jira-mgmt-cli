"""Unit tests for JiraClient's request building, TLS verification toggle, and error mapping."""

from __future__ import annotations

import httpx
import pytest

from jira_cli.client.exceptions import AuthenticationError, NotFoundError
from jira_cli.client.jira_client import JiraClient
from jira_cli.config.settings import Settings


def make_settings() -> Settings:
    return Settings(
        jira_url="https://example.atlassian.net",
        jira_email="devops@example.com",
        jira_api_token="secret-token",
    )


def test_verify_ssl_defaults_to_true(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    original_init = httpx.Client.__init__

    def fake_init(self: httpx.Client, *args: object, **kwargs: object) -> None:
        captured.update(kwargs)
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.Client, "__init__", fake_init)

    JiraClient(make_settings())

    assert captured["verify"] is True


def test_no_verify_ssl_disables_certificate_verification(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    original_init = httpx.Client.__init__

    def fake_init(self: httpx.Client, *args: object, **kwargs: object) -> None:
        captured.update(kwargs)
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.Client, "__init__", fake_init)

    JiraClient(make_settings(), verify_ssl=False)

    assert captured["verify"] is False


def test_get_maps_401_to_authentication_error(monkeypatch: pytest.MonkeyPatch) -> None:
    client = JiraClient(make_settings())

    def fake_request(method: str, url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(401, json={"errorMessages": ["Unauthorized"]})

    monkeypatch.setattr(client._http, "request", fake_request)

    with pytest.raises(AuthenticationError):
        client.get("/myself")

    client.close()


def test_get_maps_404_to_not_found_error(monkeypatch: pytest.MonkeyPatch) -> None:
    client = JiraClient(make_settings())

    def fake_request(method: str, url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(404, json={"errorMessages": ["Issue does not exist"]})

    monkeypatch.setattr(client._http, "request", fake_request)

    with pytest.raises(NotFoundError):
        client.get("/issue/PROJ-999")

    client.close()


def test_post_with_files_sends_multipart_not_json(monkeypatch: pytest.MonkeyPatch) -> None:
    client = JiraClient(make_settings())
    captured: dict[str, object] = {}

    def fake_request(method: str, url: str, **kwargs: object) -> httpx.Response:
        captured.update(kwargs)
        return httpx.Response(200, json=[])

    monkeypatch.setattr(client._http, "request", fake_request)

    client.post(
        "/issue/PROJ-123/attachments",
        files=[("file", ("a.zip", b"data", "application/octet-stream"))],
        headers={"X-Atlassian-Token": "no-check"},
    )

    assert "files" in captured
    assert "json" not in captured
    assert captured["headers"] == {"X-Atlassian-Token": "no-check"}

    client.close()
