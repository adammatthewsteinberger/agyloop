"""Capacity probe: cheapest throwaway chat, no conversation_id, counted in budget."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from google.antigravity.types import BuiltinTools

from agyloop.infrastructure.agent.options import build_local_config
from agyloop.infrastructure.agent.probe import (
    AntigravityCapacityProbe,
    build_probe_config,
)


class _FakeResponse:
    async def text(self) -> str:
        return "OK"

    async def structured_output(self) -> None:
        return None


class _FakeAgent:
    def __init__(self, config: object) -> None:
        self.config = config
        self.conversation_id = None
        self.prompts: list[str] = []
        self.closed = False

    async def __aenter__(self) -> _FakeAgent:
        return self

    async def __aexit__(self, *args: object) -> None:
        self.closed = True

    async def chat(self, prompt: str) -> _FakeResponse:
        self.prompts.append(prompt)
        return _FakeResponse()


def test_probe_config_has_no_conversation_id() -> None:
    cfg = build_probe_config(cwd=".")
    assert cfg.conversation_id is None


def test_probe_config_forwards_input_detection_override() -> None:
    from agyloop.domain.model_profile import INPUT_DETECTION_MODEL

    cfg = build_probe_config(cwd=".", model="gemini-2.5-flash", api_key="test-key")
    assert cfg.env is not None
    assert cfg.env["AGYLOOP_INPUT_DETECTION_MODEL"] == INPUT_DETECTION_MODEL
    names = [m.name for m in (cfg.models or [])]
    assert INPUT_DETECTION_MODEL in names


def test_probe_config_uses_none_or_read_only_tools() -> None:
    cfg = build_probe_config(cwd=".")
    tools = list(cfg.capabilities.enabled_tools or ())
    allowed = set(BuiltinTools.none()) | set(BuiltinTools.read_only())
    assert set(tools) <= allowed
    assert BuiltinTools.RUN_COMMAND not in tools
    assert cfg.mcp_servers in (None, [])


def test_live_config_pins_empty_mcp_servers_like_probe() -> None:
    """Live SDK session must pin mcp_servers=[] the same as probe (no MCP OAuth)."""
    probe = build_probe_config(cwd=".")
    live = build_local_config(cwd=".")
    assert "mcp_servers" in probe.model_fields_set
    assert probe.mcp_servers == []
    assert "mcp_servers" in live.model_fields_set
    assert live.mcp_servers == []


@pytest.fixture
def fake_probe_agent() -> _FakeAgent:
    agent = _FakeAgent(config=None)

    def _factory(config: object) -> _FakeAgent:
        agent.config = config
        return agent

    with patch("agyloop.infrastructure.agent.probe.Agent", side_effect=_factory):
        yield agent


async def test_probe_issues_single_chat_without_conversation_id(
    fake_probe_agent: _FakeAgent,
) -> None:
    probe = AntigravityCapacityProbe(cwd=".")
    outcome = await probe.probe()
    assert fake_probe_agent.config.conversation_id is None
    assert len(fake_probe_agent.prompts) == 1
    assert fake_probe_agent.closed is True
    assert outcome.session_id is None
