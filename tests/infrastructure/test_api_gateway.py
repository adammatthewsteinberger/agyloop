"""Gemini REST gateway: path interpolation, fake transport, lane split."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agyloop.infrastructure.api.gateway import GeminiRestGateway, interpolate_path


class _FakeTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, str], bytes | None]] = []

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None,
    ) -> tuple[int, str]:
        self.calls.append((method, url, headers, body))
        return 200, json.dumps({"ok": True, "url": url})


def test_interpolate_plus_name() -> None:
    path, leftover = interpolate_path("v1beta/{+name}:cancel", {"name": "batches/abc", "foo": 1})
    assert path == "v1beta/batches/abc:cancel"
    assert leftover == {"foo": 1}


def test_invoke_posts_json_with_developer_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    transport = _FakeTransport()
    gateway = GeminiRestGateway(transport=transport)
    result = gateway.invoke(
        "models.generateContent",
        json_body=json.dumps({"model": "models/gemini-2.5-pro", "contents": []}),
    )
    assert result["ok"] is True
    method, url, _headers, body = transport.calls[0]
    assert method == "POST"
    assert "generativelanguage.googleapis.com" in url
    assert "key=test-key" in url
    assert body is not None
    payload = json.loads(body.decode())
    assert payload["contents"] == []


def test_vertex_lane_invokes_aiplatform(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_ACCESS_TOKEN", "ya29.test")
    transport = _FakeTransport()
    gateway = GeminiRestGateway(transport=transport)
    result = gateway.invoke(
        "projects.locations.publishers.models.generateContent",
        lane="vertex",
        json_body=json.dumps(
            {
                "model": (
                    "projects/p/locations/us-central1/publishers/google/models/gemini-2.5-flash"
                ),
                "contents": [],
            }
        ),
    )
    assert result["ok"] is True
    method, url, headers, _body = transport.calls[0]
    assert method == "POST"
    assert "aiplatform.googleapis.com" in url
    assert headers["Authorization"] == "Bearer ya29.test"


def test_missing_api_key_is_loud(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    gateway = GeminiRestGateway(transport=_FakeTransport())
    with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
        gateway.invoke(
            "models.generateContent",
            json_body=json.dumps({"model": "models/gemini-2.5-pro"}),
        )
