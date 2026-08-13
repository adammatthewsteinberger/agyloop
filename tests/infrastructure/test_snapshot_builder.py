"""Snapshot builder writes JSON under .agyloop/runs/<id>/snapshots/."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from agyloop.infrastructure.rundir import RunDirectory, runs_root_for
from agyloop.infrastructure.snapshot import RunSnapshotBuilder


class _FrozenClock:
    def now(self) -> datetime:
        return datetime(2026, 8, 13, 12, 0, tzinfo=UTC)


def test_manual_snapshot_writes_latest_and_bundle(tmp_path: Path) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    directory.update_meta(conversation_id="conv-snap", status="finished")
    builder = RunSnapshotBuilder(directory)
    ref = builder.emit("manual", context={"session_id": "conv-snap"})
    assert ref is not None
    assert ref.reason == "manual"
    assert (directory.root / "snapshots" / "latest.json").is_file()
    assert (directory.root / ref.path).is_file()
    assert ref.bundle_path is not None
    assert (directory.root / ref.bundle_path / "snapshot.json").is_file()


def test_status_snapshot_skips_duplicate_digest(tmp_path: Path) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    builder = RunSnapshotBuilder(directory, clock=_FrozenClock())
    first = builder.emit("status", bundle=False)
    second = builder.emit("status", bundle=False)
    assert first is not None
    assert second is None
