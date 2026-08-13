"""Git save-point store: refs/agyloop, ignore .agyloop/, no empty commits."""

from __future__ import annotations

import subprocess
from pathlib import Path

from agyloop.infrastructure.git_savepoints import GitSavePointStore
from agyloop.infrastructure.rundir import RunDirectory, runs_root_for


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(  # nosec B603
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _init_repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "agyloop@example.test")
    _git(tmp_path, "config", "user.name", "agyloop")
    (tmp_path / "README.md").write_text("hello\n", encoding="utf-8")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-m", "init")
    return tmp_path


def test_create_commits_worktree_and_ignores_agyloop_dir(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    run_dir = RunDirectory.create(runs_root_for(repo), cwd=repo)
    (repo / "src.txt").write_text("work\n", encoding="utf-8")
    store = GitSavePointStore(cwd=repo, index_path=run_dir.savepoints_path)
    run_id = run_dir.read_meta().run_id
    point = store.create(run_id=run_id, label="turn", attempt=1, summary="did work")
    assert point is not None
    assert point.committed is True
    assert point.ref.startswith("refs/agyloop/")
    subject = _git(repo, "log", "-1", "--format=%s")
    assert subject.startswith("chore(agyloop):")
    assert ".agyloop" not in _git(repo, "ls-tree", "-r", "--name-only", "HEAD")
    listed = store.list_points(run_dir.read_meta().run_id)
    assert len(listed) == 1
    assert listed[0].sha == point.sha


def test_create_skips_pycache_and_bytecode(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    run_dir = RunDirectory.create(runs_root_for(repo), cwd=repo)
    (repo / "pkg").mkdir()
    (repo / "pkg" / "mod.py").write_text("x = 1\n", encoding="utf-8")
    pycache = repo / "pkg" / "__pycache__"
    pycache.mkdir()
    (pycache / "mod.cpython-312.pyc").write_bytes(b"\0pyc")
    (repo / "pkg" / "mod.pyo").write_bytes(b"\0pyo")
    store = GitSavePointStore(cwd=repo, index_path=run_dir.savepoints_path)
    run_id = run_dir.read_meta().run_id
    point = store.create(run_id=run_id, label="turn", attempt=1, summary="code")
    assert point is not None
    assert point.committed is True
    names = _git(repo, "ls-tree", "-r", "--name-only", "HEAD")
    assert "pkg/mod.py" in names
    assert "__pycache__" not in names
    assert "mod.pyo" not in names


def test_unchanged_tree_is_ref_only_no_empty_commit(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    run_dir = RunDirectory.create(runs_root_for(repo), cwd=repo)
    store = GitSavePointStore(cwd=repo, index_path=run_dir.savepoints_path)
    run_id = run_dir.read_meta().run_id
    first = store.create(run_id=run_id, label="a", attempt=1)
    assert first is not None
    head_before = _git(repo, "rev-parse", "HEAD")
    second = store.create(run_id=run_id, label="b", attempt=2)
    assert second is not None
    assert second.committed is False
    assert second.sha == head_before
    assert _git(repo, "rev-parse", "HEAD") == head_before


def test_unwind_hard_resets_to_savepoint(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    run_dir = RunDirectory.create(runs_root_for(repo), cwd=repo)
    store = GitSavePointStore(cwd=repo, index_path=run_dir.savepoints_path)
    run_id = run_dir.read_meta().run_id
    (repo / "one.txt").write_text("one\n", encoding="utf-8")
    first = store.create(run_id=run_id, label="one", attempt=1)
    assert first is not None
    (repo / "two.txt").write_text("two\n", encoding="utf-8")
    store.create(run_id=run_id, label="two", attempt=2)
    result = store.unwind(run_id=run_id, to="1", backup=True)
    assert result.restored_sha == first.sha
    assert result.backup_ref is not None
    assert result.backup_ref.startswith("refs/agyloop/backup/")
    assert not (repo / "two.txt").exists()
    assert (repo / "one.txt").is_file()
