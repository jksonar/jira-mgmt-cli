"""Unit tests for the Microsoft Teams webhook notifier."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from jira_cli.client.exceptions import NetworkError
from jira_cli.services.teams_service import post_teams_message


class _FakeResponse:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


def test_post_teams_message_sends_adaptive_card(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_post(url: str, json: dict[str, Any] | None = None, timeout: float | None = None) -> Any:
        captured["url"] = url
        captured["json"] = json
        return _FakeResponse(200)

    monkeypatch.setattr(httpx, "post", fake_post)

    post_teams_message("https://example.com/webhook", "Deployed 25.10.3")

    assert captured["url"] == "https://example.com/webhook"
    assert captured["json"] == {
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "type": "AdaptiveCard",
                    "version": "1.0",
                    "body": [{"type": "TextBlock", "text": "Deployed 25.10.3"}],
                },
            }
        ]
    }


def test_post_teams_message_raises_on_error_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _FakeResponse(500, "boom"))

    with pytest.raises(NetworkError):
        post_teams_message("https://example.com/webhook", "hi")


def test_post_teams_message_wraps_network_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_request_error(*args: Any, **kwargs: Any) -> Any:
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "post", raise_request_error)

    with pytest.raises(NetworkError):
        post_teams_message("https://example.com/webhook", "hi")
