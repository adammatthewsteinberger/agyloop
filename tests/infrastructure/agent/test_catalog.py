"""Run registry catalog — our .agyloop/runs, never vendor conversations."""

from __future__ import annotations

from pathlib import Path

from agyloop.infrastructure.agent.catalog import RunRegistryCatalog
from agyloop.infrastructure.rundir import RunDirectory, runs_root_for


def test_catalog_lists_only_agyloop_runs(tmp_path: Path) -> None:
    first = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    first.update_meta(conversation_id="conv-1")
    second = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    second.update_meta(conversation_id="conv-2")
    (tmp_path / ".claude" / "projects").mkdir(parents=True)
    (tmp_path / ".claude" / "projects" / "vendor-session.jsonl").write_text("x")

    catalog = RunRegistryCatalog()
    refs = catalog.list_all(str(tmp_path))
    ids = {ref.session_id for ref in refs}
    assert ids == {"conv-1", "conv-2"}
    assert all(ref.cwd == str(tmp_path.resolve()) for ref in refs)


def test_catalog_uses_run_id_when_conversation_id_missing(tmp_path: Path) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    catalog = RunRegistryCatalog()
    refs = catalog.list_all(str(tmp_path))
    assert len(refs) == 1
    assert refs[0].session_id == directory.read_meta().run_id


def test_most_recent_returns_latest_run(tmp_path: Path) -> None:
    RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path).update_meta(conversation_id="older")
    RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path).update_meta(conversation_id="newer")
    catalog = RunRegistryCatalog()
    ref = catalog.most_recent(str(tmp_path))
    assert ref is not None
    assert ref.session_id == "newer"


def test_catalog_empty_when_no_registry(tmp_path: Path) -> None:
    catalog = RunRegistryCatalog()
    assert catalog.list_all(str(tmp_path)) == []
    assert catalog.most_recent(str(tmp_path)) is None


def test_catalog_skips_directories_without_meta(tmp_path: Path) -> None:
    RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path).update_meta(conversation_id="kept")
    (runs_root_for(tmp_path) / "not-a-run").mkdir(parents=True)
    catalog = RunRegistryCatalog()
    refs = catalog.list_all(str(tmp_path))
    assert {ref.session_id for ref in refs} == {"kept"}
