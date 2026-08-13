"""Operator use cases for mid-run control — port-shaped, no infrastructure imports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from agyloop.domain.control import (
    ControlCommand,
    PromptDeferredCommand,
    PromptNowCommand,
    StopCommand,
)


class ControlInbox(Protocol):
    def enqueue(self, command: ControlCommand) -> object: ...


@dataclass(frozen=True, slots=True)
class EnqueueResult:
    run_id: str
    command_type: str


def request_stop(inbox: ControlInbox, *, run_id: str) -> EnqueueResult:
    inbox.enqueue(StopCommand())
    return EnqueueResult(run_id=run_id, command_type="stop")


def request_prompt(
    inbox: ControlInbox, text: str, *, immediate: bool, run_id: str
) -> EnqueueResult:
    command: ControlCommand = (
        PromptNowCommand(text=text) if immediate else PromptDeferredCommand(text=text)
    )
    inbox.enqueue(command)
    return EnqueueResult(
        run_id=run_id,
        command_type="prompt_now" if immediate else "prompt_deferred",
    )
