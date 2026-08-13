"""File-based RunControl inbox under .agyloop/runs/<id>/inbox/."""

from __future__ import annotations

from pathlib import Path

from agyloop.domain.control import (
    PromptNowCommand,
    SetModelCommand,
    SetPresetCommand,
    StopCommand,
)
from agyloop.infrastructure.control import FileRunControl


def test_file_run_control_prompt_roundtrip(tmp_path: Path) -> None:
    control = FileRunControl(tmp_path / "inbox")
    control.enqueue(PromptNowCommand(text="hello"))
    assert control.poll() == [PromptNowCommand(text="hello")]
    assert control.poll() == []


def test_file_run_control_stop_outranks_prompt(tmp_path: Path) -> None:
    control = FileRunControl(tmp_path / "inbox")
    control.enqueue(PromptNowCommand(text="hello"))
    control.enqueue(StopCommand())
    assert control.poll() == [StopCommand()]


def test_file_run_control_model_and_preset_roundtrip(tmp_path: Path) -> None:
    control = FileRunControl(tmp_path / "inbox")
    control.enqueue(SetModelCommand(model="gemini-2.5-pro"))
    control.enqueue(SetPresetCommand(preset="high"))
    polled = control.poll()
    assert SetPresetCommand(preset="high") in polled
    assert SetModelCommand(model="gemini-2.5-pro") in polled
