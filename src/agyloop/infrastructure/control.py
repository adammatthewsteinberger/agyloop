"""File-based RunControl — operator commands land in inbox/*.cmd.json."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from agyloop.domain.control import (
    ControlCommand,
    PromptDeferredCommand,
    PromptNowCommand,
    StopCommand,
    stop_outranks,
)


class FileRunControl:
    def __init__(self, inbox: Path) -> None:
        self._inbox = inbox
        self._inbox.mkdir(parents=True, exist_ok=True)

    def enqueue(self, command: ControlCommand) -> Path:
        payload = _command_to_payload(command)
        name = f"{time.time_ns()}-{payload['type']}.cmd.json"
        path = self._inbox / name
        path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        return path

    def poll(self) -> list[ControlCommand]:
        files = sorted(self._inbox.glob("*.cmd.json"))
        commands: list[ControlCommand] = []
        for path in files:
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                commands.append(_payload_to_command(raw))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue
            else:
                path.unlink(missing_ok=True)
        return stop_outranks(commands)


def _command_to_payload(command: ControlCommand) -> dict[str, Any]:
    match command:
        case StopCommand():
            return {"type": "stop"}
        case PromptNowCommand(text=text):
            return {"type": "prompt_now", "text": text}
        case PromptDeferredCommand(text=text):
            return {"type": "prompt_deferred", "text": text}
        case _:
            raise TypeError(f"unsupported control command: {type(command)!r}")


def _payload_to_command(raw: dict[str, object]) -> ControlCommand:
    kind = str(raw["type"])
    if kind == "stop":
        return StopCommand()
    if kind == "prompt_now":
        return PromptNowCommand(text=str(raw["text"]))
    if kind == "prompt_deferred":
        return PromptDeferredCommand(text=str(raw["text"]))
    raise ValueError(f"unknown control command type: {kind}")
