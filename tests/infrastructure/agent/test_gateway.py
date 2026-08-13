"""SDK gateway wraps Agent(config) as an async CM and maps drain errors."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from google.antigravity.types import AntigravityExecutionError, AntigravityValidationError

from agyloop.application.dto import TurnOutcome
from agyloop.domain.classify import TurnSignals
from agyloop.domain.errors import AgentConfigError
from agyloop.infrastructure.agent.gateway import AntigravityAgentGateway


class _FakeResponse:
    def __init__(
        self,
        *,
        text: str = "",
        error: BaseException | None = None,
        structured: dict[str, object] | None = None,
    ) -> None:
        self._text = text
        self._error = error
        self._structured = structured

    async def text(self) -> str:
        if self._error is not None:
            raise self._error
        return self._text

    async def structured_output(self) -> dict[str, object] | None:
        if self._error is not None:
            raise self._error
        return self._structured

    async def resolve(self) -> list[object]:
        if self._error is not None:
            raise self._error
        return []


class _FakeAgent:
    def __init__(self, config: object) -> None:
        self.config = config
        self.conversation_id = "c" * 32
        self.prompts: list[str] = []
        self.closed = False
        self.response: _FakeResponse = _FakeResponse(text="ok")

    async def __aenter__(self) -> _FakeAgent:
        return self

    async def __aexit__(self, *args: object) -> None:
        self.closed = True

    async def chat(self, prompt: str) -> _FakeResponse:
        self.prompts.append(prompt)
        return self.response


@pytest.fixture
def fake_agent() -> _FakeAgent:
    agent = _FakeAgent(config=None)

    def _factory(config: object) -> _FakeAgent:
        agent.config = config
        return agent

    with patch("agyloop.infrastructure.agent.gateway.Agent", side_effect=_factory):
        yield agent


async def test_send_turn_drains_chat_and_returns_turn_outcome(fake_agent: _FakeAgent) -> None:
    fake_agent.response = _FakeResponse(text="hello from gemini")
    gateway = AntigravityAgentGateway(cwd=".")
    outcome = await gateway.send_turn("do the work")
    await gateway.close()
    assert isinstance(outcome, TurnOutcome)
    assert isinstance(outcome.signals, TurnSignals)
    assert outcome.output_text == "hello from gemini"
    assert outcome.session_id == "c" * 32
    assert fake_agent.prompts == ["do the work"]
    assert fake_agent.closed is True


async def test_send_turn_maps_execution_error_to_signals(fake_agent: _FakeAgent) -> None:
    fake_agent.response = _FakeResponse(
        error=AntigravityExecutionError("429 RESOURCE_EXHAUSTED: quota")
    )
    gateway = AntigravityAgentGateway(cwd=".")
    outcome = await gateway.send_turn("go")
    await gateway.close()
    assert outcome.signals.exception_type == "AntigravityExecutionError"
    assert outcome.signals.http_status == 429
    assert outcome.session_id == "c" * 32


async def test_send_turn_validation_error_is_our_bug(fake_agent: _FakeAgent) -> None:
    fake_agent.response = _FakeResponse(error=AntigravityValidationError("invalid config field"))
    gateway = AntigravityAgentGateway(cwd=".")
    with pytest.raises(AgentConfigError):
        await gateway.send_turn("go")
    await gateway.close()


async def test_send_turn_does_not_return_vendor_types(fake_agent: _FakeAgent) -> None:
    gateway = AntigravityAgentGateway(cwd=".")
    outcome = await gateway.send_turn("go")
    await gateway.close()
    assert "antigravity" not in type(outcome).__module__
    assert "antigravity" not in type(outcome.signals).__module__


async def test_set_permission_mode_accepts_agyloop_enum_not_vendor_types(
    fake_agent: _FakeAgent,
) -> None:
    gateway = AntigravityAgentGateway(cwd=".")
    await gateway.set_permission_mode("scoped")
    await gateway.send_turn("go")
    await gateway.close()
    assert fake_agent.config is not None
