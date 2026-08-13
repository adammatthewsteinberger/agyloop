"""File-based RunControl inbox under .agyloop/runs/<id>/inbox/."""

from __future__ import annotations

from pathlib import Path

from agyloop.domain.control import PromptNowCommand, StopCommand
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
