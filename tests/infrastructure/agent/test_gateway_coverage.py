from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.antigravity.types import (
    AntigravityConnectionError,
    AntigravityExecutionError,
    AntigravityValidationError,
)

from agyloop.domain.model_profiles import ModelEffortProfile
from agyloop.infrastructure.agent.gateway import (
    AntigravityAgentGateway,
    _usage_tokens,
)


def test_usage_tokens_variants() -> None:
    assert _usage_tokens(None, "prompt") == 0
    assert _usage_tokens(object(), "prompt") == 0

    # usage as object with prompt_tokens
    class UsageObj:
        prompt_tokens = 10
        candidates_token_count = 20

    class RespObj:
        usage_metadata = UsageObj()

    assert _usage_tokens(RespObj(), "prompt") == 10
    assert _usage_tokens(RespObj(), "completion") == 20

    # usage as dict
    class RespDict:
        usage = {"input_tokens": 15, "output_tokens": 25}

    assert _usage_tokens(RespDict(), "prompt") == 15
    assert _usage_tokens(RespDict(), "completion") == 25


async def test_gateway_methods_and_reconnect() -> None:
    events = []
    gateway = AntigravityAgentGateway(
        cwd="/tmp/dir1",
        model="gemini-2.5-flash",
        add_dirs=["/tmp/extra"],
        system_prompt_append="extra prompt",
        on_event=lambda e: events.append(e),
    )

    assert gateway.resolve_tool_approval("req1", allow=True) is False

    # set_profile: same model (no reconnect) vs new model (reconnect)
    await gateway.set_profile(ModelEffortProfile(model="gemini-2.5-flash", effort="high"))
    with patch.object(gateway, "close", new_callable=AsyncMock) as mock_close:
        await gateway.set_profile(ModelEffortProfile(model="gemini-2.5-pro", effort="high"))
        assert mock_close.called

    # set_permission_mode: same mode vs new mode
    with patch.object(gateway, "close", new_callable=AsyncMock) as mock_close:
        await gateway.set_permission_mode("autonomous")
        assert not mock_close.called
        await gateway.set_permission_mode("scoped")
        assert mock_close.called

    # set_cwd: same cwd vs new cwd
    with patch.object(gateway, "close", new_callable=AsyncMock) as mock_close:
        await gateway.set_cwd("/tmp/dir1")
        assert not mock_close.called
        await gateway.set_cwd("/tmp/dir2")
        assert mock_close.called

    # set_session_resources: no changes vs changes
    with patch.object(gateway, "close", new_callable=AsyncMock) as mock_close:
        await gateway.set_session_resources(add_dirs=["/tmp/extra"], system_prompt_append="extra prompt")
        assert not mock_close.called
        await gateway.set_session_resources(add_dirs=["/tmp/new_extra"])
        assert mock_close.called
        mock_close.reset_mock()
        await gateway.set_session_resources(system_prompt_append="new prompt")
        assert mock_close.called


async def test_gateway_send_turn_operator_cancel_and_events() -> None:
    mock_agent = MagicMock()
    mock_agent.conversation_id = "c123"
    mock_response = MagicMock()
    mock_response.text = AsyncMock(return_value="operator canceled the run")
    mock_response.structured_output = AsyncMock(return_value=None)
    mock_response.usage_metadata = None
    mock_agent.chat = AsyncMock(return_value=mock_response)

    events = []
    gateway = AntigravityAgentGateway(
        cwd="/tmp/dir1",
        on_event=lambda e: events.append(e),
    )

    with patch("agyloop.infrastructure.agent.gateway.Agent") as mock_agent_cls:
        mock_agent_instance = AsyncMock()
        mock_agent_instance.__aenter__.return_value = mock_agent
        mock_agent_cls.return_value = mock_agent_instance

        outcome = await gateway.send_turn("do something")
        assert outcome.signals.message == "operator canceled the run"
        assert len(events) == 1
        assert events[0]["event"] == "turn_complete"
        assert events[0]["session_id"] == "c123"

        await gateway.close()


async def test_gateway_resume_degraded_without_plan_seed() -> None:
    gateway = AntigravityAgentGateway(
        cwd="/tmp/dir1",
        conversation_id="conv_old",
        plan_seed=None,
    )
    assert gateway._seeded_prompt("my prompt") == "my prompt"


async def test_gateway_exception_when_ensure_started_fails() -> None:
    gateway = AntigravityAgentGateway(cwd="/tmp/dir1")
    with patch("agyloop.infrastructure.agent.gateway.Agent") as mock_agent_cls:
        mock_agent_instance = AsyncMock()
        mock_agent_instance.__aenter__.side_effect = AntigravityConnectionError("cannot connect to server")
        mock_agent_cls.return_value = mock_agent_instance

        with pytest.raises(AntigravityConnectionError):
            await gateway.send_turn("prompt")
