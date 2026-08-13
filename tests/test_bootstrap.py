"""Composition root wiring for adaptive wait, --no-probe, and the loud notifier."""

import inspect
from pathlib import Path

import pytest
from google.antigravity.types import BuiltinTools

from agyloop.bootstrap import build_runner, parse_gateway
from agyloop.infrastructure.agent.gateway import AntigravityAgentGateway
from agyloop.infrastructure.agent.gateway_cli import AgyCliAgentGateway
from agyloop.infrastructure.control import FileRunControl
from agyloop.infrastructure.git_savepoints import GitSavePointStore
from agyloop.infrastructure.notify import StderrNotifier
from agyloop.infrastructure.snapshot import RunSnapshotBuilder


def test_build_runner_wires_no_probe_and_stderr_notifier(tmp_path: Path) -> None:
    context = build_runner(cwd=tmp_path, no_probe=True)
    assert context.runner._no_probe is True
    assert context.runner._wait_policy.no_probe is True
    assert isinstance(context.runner._notifier, StderrNotifier)
    assert isinstance(context.runner._control, FileRunControl)
    assert isinstance(context.runner._save_points, GitSavePointStore)
    assert isinstance(context.runner._snapshots, RunSnapshotBuilder)
    assert context.runner._ramp == 0


def test_build_runner_strict_autonomy_disables_ask_question(tmp_path: Path) -> None:
    source = inspect.getsource(build_runner)
    assert "del strict_autonomy" not in source
    context = build_runner(cwd=tmp_path, strict_autonomy=True)
    assert isinstance(context.gateway, AntigravityAgentGateway)
    cfg = context.gateway._config()
    assert BuiltinTools.ASK_QUESTION in (cfg.capabilities.disabled_tools or [])


def test_build_runner_passes_google_api_key_into_sdk_gateway(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    context = build_runner(cwd=tmp_path, no_probe=True)
    assert isinstance(context.gateway, AntigravityAgentGateway)
    assert context.gateway._api_key == "test-google-key"
    assert context.gateway._config().api_key == "test-google-key"


def test_build_runner_cli_gateway_and_ramp(tmp_path: Path) -> None:
    context = build_runner(cwd=tmp_path, gateway="cli", ramp=4, no_probe=True)
    assert isinstance(context.gateway, AgyCliAgentGateway)
    assert context.runner._ramp == 4
    assert parse_gateway("SDK") == "sdk"
    assert parse_gateway("cli") == "cli"
