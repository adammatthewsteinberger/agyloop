"""HITL / ask_question is denied with guidance, never auto-answered."""

from __future__ import annotations

import inspect

from google.antigravity.hooks.hooks import HookContext
from google.antigravity.types import BuiltinTools, ToolCall

from agyloop.infrastructure.agent.autonomy import (
    ASK_QUESTION_DENY_MESSAGE,
    DenyAskQuestionHook,
)


async def test_ask_question_denied_with_guidance() -> None:
    hook = DenyAskQuestionHook()
    result = await hook.run(HookContext(), ToolCall(name=BuiltinTools.ASK_QUESTION, args={}))
    assert result.allow is False
    assert result.message == ASK_QUESTION_DENY_MESSAGE
    assert "no human is available" in result.message
    assert "Do not call `ask_question` again" in result.message


async def test_ask_question_deny_does_not_block_other_tools() -> None:
    hook = DenyAskQuestionHook()
    result = await hook.run(
        HookContext(), ToolCall(name=BuiltinTools.VIEW_FILE, args={"path": "a.py"})
    )
    assert result.allow is True


def test_ask_question_handler_is_synchronous() -> None:
    """The decide body must not await a human; SDK run() is async but we don't wait."""
    source = inspect.getsource(DenyAskQuestionHook.run)
    assert "input(" not in source
    assert "async_input" not in source
    assert "sleep(" not in source
