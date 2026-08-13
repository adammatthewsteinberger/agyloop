"""Per-run control directory under `.agyloop/runs/<run_id>/`."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from agyloop.infrastructure.rundir import (
    RunDirectory,
    list_run_directories,
    resolve_run_directory,
    runs_root_for,
)


def test_runs_root_is_dot_agyloop(tmp_path: Path) -> None:
    assert runs_root_for(tmp_path) == tmp_path / ".agyloop" / "runs"


def test_create_writes_meta_without_conversation_id(tmp_path: Path) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text("- [ ] do it\n", encoding="utf-8")
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path, plan_path=plan)
    assert directory.meta_path.is_file()
    meta = directory.read_meta()
    assert meta.conversation_id is None
    assert meta.plan_path is not None
    assert Path(meta.plan_path).name == "plan.md"
    assert (directory.root / "plan.md").is_file()


def test_update_meta_persists_conversation_id_after_first_turn(tmp_path: Path) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    directory.update_meta(conversation_id="c" * 32)
    assert directory.read_meta().conversation_id == "c" * 32
    directory.update_meta(session_id="from-runner")
    assert directory.read_meta().conversation_id == "from-runner"


def test_update_meta_preserves_conversation_id_when_session_id_is_none(
    tmp_path: Path,
) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    original = "conv-resume-id"
    directory.update_meta(conversation_id=original)
    directory.update_meta(session_id=None, phase="WAITING", status="waiting")
    meta = directory.read_meta()
    assert meta.conversation_id == original
    assert meta.status == "waiting"


def test_write_meta_fsyncs(tmp_path: Path) -> None:
    synced: list[int] = []
    real_fsync = os.fsync

    def _spy(fd: int) -> None:
        synced.append(fd)
        real_fsync(fd)

    with patch("agyloop.infrastructure.rundir.os.fsync", side_effect=_spy):
        RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    assert synced


def test_list_run_directories_is_empty_when_missing(tmp_path: Path) -> None:
    assert list_run_directories(tmp_path) == []


def test_resolve_run_directory_prefers_explicit_id(tmp_path: Path) -> None:
    first = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    second = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    resolved = resolve_run_directory(tmp_path, run_id=first.read_meta().run_id)
    assert resolved.root == first.root
    latest = resolve_run_directory(tmp_path)
    assert latest.root == second.root
