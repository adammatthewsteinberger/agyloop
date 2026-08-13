"""Localhost Gemini rewrite proxy — withdrawn model id only, no live Google."""

from __future__ import annotations

import urllib.request

import pytest

from agyloop.domain.classify import WITHDRAWN_INPUT_DETECTION_MODEL
from agyloop.domain.model_profile import INPUT_DETECTION_MODEL
from agyloop.infrastructure.agent.gemini_rewrite import (
    GeminiRewriteProxy,
    rewrite_withdrawn_model_bytes,
    rewrite_withdrawn_model_text,
    should_install_rewrite_ca,
)


def test_rewrite_withdrawn_model_in_path_and_body() -> None:
    path = f"/v1beta/models/{WITHDRAWN_INPUT_DETECTION_MODEL}:generateContent"
    assert INPUT_DETECTION_MODEL in rewrite_withdrawn_model_text(path)
    assert WITHDRAWN_INPUT_DETECTION_MODEL not in rewrite_withdrawn_model_text(path)
    body = f'{{"model":"{WITHDRAWN_INPUT_DETECTION_MODEL}"}}'.encode()
    rewritten = rewrite_withdrawn_model_bytes(body)
    assert INPUT_DETECTION_MODEL.encode() in rewritten
    assert WITHDRAWN_INPUT_DETECTION_MODEL.encode() not in rewritten


def test_proxy_refuses_non_loopback() -> None:
    with pytest.raises(ValueError, match="loopback"):
        GeminiRewriteProxy(listen_host="0.0.0.0")


def test_rewrite_proxy_rewrites_path_before_origin() -> None:
    seen: list[tuple[str, str, bytes]] = []

    def transport(
        method: str, path: str, body: bytes, headers: dict[str, str]
    ) -> tuple[int, bytes, dict[str, str]]:
        del headers
        seen.append((method, path, body))
        return 200, b'{"ok":true}', {"Content-Type": "application/json"}

    proxy = GeminiRewriteProxy(listen_host="127.0.0.1", transport=transport)
    url = proxy.start()
    try:
        req = urllib.request.Request(
            f"{url}/v1beta/models/{WITHDRAWN_INPUT_DETECTION_MODEL}:generateContent",
            data=f'{{"model":"{WITHDRAWN_INPUT_DETECTION_MODEL}"}}'.encode(),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as response:  # nosec B310
            assert response.status == 200
            assert response.read() == b'{"ok":true}'
    finally:
        proxy.stop()
    assert seen
    method, path, body = seen[0]
    assert method == "POST"
    assert WITHDRAWN_INPUT_DETECTION_MODEL not in path
    assert INPUT_DETECTION_MODEL in path
    assert WITHDRAWN_INPUT_DETECTION_MODEL.encode() not in body


def test_rewrite_ca_install_is_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AGYLOOP_INSTALL_REWRITE_CA", raising=False)
    assert should_install_rewrite_ca() is False
    monkeypatch.setenv("AGYLOOP_INSTALL_REWRITE_CA", "1")
    assert should_install_rewrite_ca() is True
