from __future__ import annotations

import re
from pathlib import Path

import pytest
from typer.testing import CliRunner, Result

from agyloop import __version__
from agyloop.cli.app import app

runner = CliRunner()

_NO_COLOR_ENV = {"NO_COLOR": "1", "TERM": "dumb", "FORCE_COLOR": "0"}
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


def _invoke(*args: str, env: dict[str, str] | None = None) -> Result:
    merged = dict(_NO_COLOR_ENV)
    if env:
        merged.update(env)
    return runner.invoke(app, list(args), env=merged)


def _plain(text: str) -> str:
    return _ANSI_ESCAPE.sub("", text)


def test_version_option_reports_installed_version() -> None:
    result = _invoke("--version")

    assert result.exit_code == 0
    assert result.stdout.strip() == f"agyloop {__version__}"


def test_help_option_succeeds() -> None:
    result = _invoke("--help")

    assert result.exit_code == 0
    stdout = _plain(result.stdout)
    assert "Autonomous Google Antigravity" in stdout
    assert "run" in stdout
    assert "resume" in stdout
    assert "sessions" in stdout
    assert "doctor" in stdout


def test_run_help_renders() -> None:
    result = _invoke("run", "--help")

    assert result.exit_code == 0
    stdout = _plain(result.stdout)
    assert "PLAN" in stdout.upper() or "plan" in stdout
    assert "--no-probe" in stdout
    assert "--model" in stdout
    assert "--max-turns" in stdout
    assert "--max-wait" in stdout


def test_resume_help_renders() -> None:
    result = _invoke("resume", "--help")

    assert result.exit_code == 0
    stdout = _plain(result.stdout)
    assert "--conversation" in stdout
    assert "--last" in stdout


def test_sessions_help_states_registry_only_limitation() -> None:
    result = _invoke("sessions", "--help")

    assert result.exit_code == 0
    stdout = _plain(result.stdout).lower()
    assert "cannot enumerate" in stdout or "cannot list vendor" in stdout
    assert "vendor" in stdout or "conversation" in stdout


def test_doctor_help_renders() -> None:
    result = _invoke("doctor", "--help")

    assert result.exit_code == 0
    stdout = _plain(result.stdout).lower()
    assert "auth" in stdout or "google_api_key" in stdout or "pre-flight" in stdout


def test_cli_package_does_not_import_infrastructure() -> None:
    root = Path(__file__).parents[1] / "src" / "agyloop" / "cli"
    source = "\n".join(path.read_text() for path in root.rglob("*.py"))
    assert "agyloop.infrastructure" not in source


def test_async_bridge_is_asyncio_run() -> None:
    from agyloop.cli import asyncio as cli_asyncio

    assert hasattr(cli_asyncio, "async_command")
    source = (Path(__file__).parents[1] / "src" / "agyloop" / "cli" / "asyncio.py").read_text()
    calls = [
        line
        for line in source.splitlines()
        if "asyncio.run(" in line and not line.strip().startswith("#")
    ]
    assert len(calls) == 1


def test_doctor_cli_reports_resolved_lane(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from agyloop.application.usecases.doctor import AuthResolution

    class _FakeEnv:
        def resolve_auth(self) -> AuthResolution:
            return AuthResolution(
                lane="developer_api",
                source="GOOGLE_API_KEY",
                authenticated=True,
                detail="Developer API via GOOGLE_API_KEY",
            )

        def interactive_hooks_registered(self) -> bool:
            return False

        def find_agy_cli(self) -> str | None:
            return None

        def agy_cli_version(self, path: str) -> str | None:
            del path
            return None

        def configured_mcp_servers(self) -> list[str]:
            return []

    monkeypatch.setattr("agyloop.bootstrap.build_doctor_environment", lambda: _FakeEnv())
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    result = _invoke("doctor")
    assert result.exit_code == 0
    stdout = _plain(result.stdout)
    assert "developer_api" in stdout
    assert "GOOGLE_API_KEY" in stdout
    assert "AI Studio" in stdout


def test_sessions_cli_lists_registry_only(tmp_path: Path) -> None:
    from agyloop.infrastructure.rundir import RunDirectory, runs_root_for

    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    directory.update_meta(conversation_id="conv-listed")
    result = _invoke("sessions", "--cwd", str(tmp_path))
    assert result.exit_code == 0
    stdout = _plain(result.stdout)
    assert "conv-listed" in stdout
    assert "cannot be enumerated" in stdout.lower() or "not vendor" in stdout.lower()


def test_run_cli_uses_bootstrap_runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from agyloop.application.dto import RunResult

    plan = tmp_path / "plan.md"
    plan.write_text("- [ ] do the thing\n", encoding="utf-8")
    seen: dict[str, object] = {}

    class _StubRunner:
        async def run(self, *, initial_prompt: str, continue_prompt: str) -> RunResult:
            seen["initial"] = initial_prompt
            del continue_prompt
            return RunResult(
                success=True,
                reason="done",
                session_id="sid",
                turns_spent=1,
                dollars_spent=0.0,
            )

    class _Ctx:
        runner = _StubRunner()
        run_id = "run-test"

    def _build_runner(**kwargs: object) -> _Ctx:
        seen["kwargs"] = kwargs
        return _Ctx()

    monkeypatch.setattr("agyloop.bootstrap.build_runner", _build_runner)
    result = _invoke("run", str(plan), "--cwd", str(tmp_path), "--no-probe")
    assert result.exception is None, result.exception
    assert result.exit_code == 0
    assert "do the thing" in str(seen["initial"])
    kwargs = seen["kwargs"]
    assert isinstance(kwargs, dict)
    assert kwargs["no_probe"] is True


def test_resume_last_seeds_from_plan_md_not_truncated_preview(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from agyloop.application.dto import RunResult
    from agyloop.bootstrap import RunnerContext, build_runner
    from agyloop.infrastructure.rundir import RunDirectory, list_run_directories, runs_root_for

    first = "Keep this heading " + ("x" * 250)
    plan = tmp_path / "source-plan.md"
    plan.write_text(f"{first}\n- [ ] second line must survive degrade seed\n", encoding="utf-8")
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path, plan_path=plan)
    directory.update_meta(conversation_id="conv-seed")
    original_run_id = directory.read_meta().run_id
    captured: dict[str, object] = {}

    class _StubRunner:
        async def run(self, *, initial_prompt: str, continue_prompt: str) -> RunResult:
            del initial_prompt, continue_prompt
            return RunResult(
                success=True,
                reason="done",
                session_id="sid",
                turns_spent=1,
                dollars_spent=0.0,
            )

    def _build_runner(**kwargs: object) -> RunnerContext:
        ctx = build_runner(**kwargs)  # type: ignore[arg-type]
        captured["cli_plan_seed"] = kwargs.get("plan_seed")
        captured["gateway_seed"] = ctx.gateway._plan_seed  # type: ignore[attr-defined]
        captured["run_id"] = ctx.run_id
        return RunnerContext(
            runner=_StubRunner(),  # type: ignore[arg-type]
            gateway=ctx.gateway,
            run_dir=ctx.run_dir,
            run_id=ctx.run_id,
            trace_id=ctx.trace_id,
        )

    monkeypatch.setattr("agyloop.bootstrap.build_runner", _build_runner)
    result = _invoke("resume", "--last", "--cwd", str(tmp_path), "--no-probe")
    assert result.exception is None, result.exception
    assert result.exit_code == 0
    cli_seed = captured["cli_plan_seed"]
    assert cli_seed != first[:200]
    gateway_seed = captured["gateway_seed"]
    assert isinstance(gateway_seed, str)
    assert "- [ ] second line must survive degrade seed" in gateway_seed
    assert captured["run_id"] == original_run_id
    assert len(list_run_directories(tmp_path)) == 1


def test_resume_last_survives_preflight_persist_of_null_session_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from agyloop.application.dto import RunResult
    from agyloop.bootstrap import RunnerContext, build_runner
    from agyloop.infrastructure.rundir import RunDirectory, runs_root_for

    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    directory.update_meta(conversation_id="conv-keep")
    directory.update_meta(session_id=None, phase="WAITING", status="waiting")
    assert directory.read_meta().conversation_id == "conv-keep"
    captured: dict[str, object] = {}

    class _StubRunner:
        async def run(self, *, initial_prompt: str, continue_prompt: str) -> RunResult:
            del initial_prompt, continue_prompt
            return RunResult(
                success=True,
                reason="done",
                session_id="sid",
                turns_spent=1,
                dollars_spent=0.0,
            )

    def _build_runner(**kwargs: object) -> RunnerContext:
        ctx = build_runner(**kwargs)  # type: ignore[arg-type]
        captured["conversation_id"] = kwargs.get("conversation_id")
        captured["run_id"] = ctx.run_id
        return RunnerContext(
            runner=_StubRunner(),  # type: ignore[arg-type]
            gateway=ctx.gateway,
            run_dir=ctx.run_dir,
            run_id=ctx.run_id,
            trace_id=ctx.trace_id,
        )

    monkeypatch.setattr("agyloop.bootstrap.build_runner", _build_runner)
    result = _invoke("resume", "--last", "--cwd", str(tmp_path), "--no-probe")
    assert result.exception is None, result.exception
    assert result.exit_code == 0
    assert captured["conversation_id"] == "conv-keep"
    assert captured["run_id"] == directory.read_meta().run_id


def test_resume_without_registry_fails_cleanly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from agyloop.domain.session import SessionRef

    class _EmptyCatalog:
        def most_recent(self, cwd: str) -> SessionRef | None:
            del cwd
            return None

        def list_all(self, cwd: str | None = None) -> list[SessionRef]:
            del cwd
            return []

    monkeypatch.setattr("agyloop.bootstrap.build_session_catalog", lambda: _EmptyCatalog())
    result = _invoke("resume", "--last", "--cwd", str(tmp_path))
    assert result.exit_code == 1
    assert (
        "cannot be enumerated" in _plain(result.output).lower()
        or "no prior" in _plain(result.output).lower()
    )
