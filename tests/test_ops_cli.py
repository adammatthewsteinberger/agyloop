from __future__ import annotations

from pathlib import Path

from agyloop.cli.app import app
from agyloop.infrastructure.rundir import RunDirectory, runs_root_for
from tests.test_cli import _invoke, _plain


def test_ops_commands_are_listed() -> None:
    result = _invoke("--help")
    assert result.exit_code == 0
    text = _plain(result.stdout).lower()
    for name in ("status", "logs", "watch", "runs", "reset", "model", "preset", "attach"):
        assert name in text


def test_run_help_includes_add_dir_and_max_dollars() -> None:
    result = _invoke("run", "--help")
    assert result.exit_code == 0
    stdout = _plain(result.stdout)
    assert "--add-dir" in stdout
    assert "--max-dollars" in stdout
    assert "--preset" in stdout
    assert "--scoped" in stdout


def test_explain_classify_reports_rung() -> None:
    result = _invoke(
        "doctor",
        "explain-classify",
        "--message",
        "spend-based rate limit",
        "--http-status",
        "429",
        "--status",
        "RESOURCE_EXHAUSTED",
    )
    assert result.exit_code == 0
    text = _plain(result.stdout)
    assert "rung=spend" in text
    assert "CreditsExhausted" in text


def test_status_and_runs_and_model_enqueue(tmp_path: Path) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    run_id = directory.read_meta().run_id
    listed = _invoke("runs", "--cwd", str(tmp_path))
    assert listed.exit_code == 0
    assert run_id in _plain(listed.stdout)
    status = _invoke("status", "--cwd", str(tmp_path), "--run-id", run_id)
    assert status.exit_code == 0
    assert run_id in _plain(status.stdout)
    queued = _invoke("model", "gemini-2.5-pro", "--cwd", str(tmp_path), "--run-id", run_id)
    assert queued.exit_code == 0
    inbox = list(directory.inbox.glob("*.cmd.json"))
    assert len(inbox) == 1
    assert "set_model" in inbox[0].read_text(encoding="utf-8")


def test_reset_refuses_without_yes(tmp_path: Path) -> None:
    RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    result = _invoke("reset", "--cwd", str(tmp_path))
    assert result.exit_code == 1
    assert "refusing" in _plain(result.output).lower()
    assert (tmp_path / ".agyloop").is_dir()


def test_reset_yes_deletes_tree(tmp_path: Path) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    directory.update_meta(status="finished")
    result = _invoke("reset", "--yes", "--cwd", str(tmp_path))
    assert result.exit_code == 0, result.output
    assert not (tmp_path / ".agyloop").exists()


def test_config_command_prints_aliases() -> None:
    result = _invoke("config")
    assert result.exit_code == 0
    text = _plain(result.stdout)
    assert "model_low:" in text
    assert "gemini-2.5" in text


def test_typer_app_exports() -> None:
    assert app.info.name == "agyloop"
