"""Composition root wiring for adaptive wait, --no-probe, and the loud notifier."""

import inspect
from pathlib import Path

from google.antigravity.types import BuiltinTools

from agyloop.bootstrap import build_runner
from agyloop.infrastructure.agent.gateway import AntigravityAgentGateway
from agyloop.infrastructure.control import FileRunControl
from agyloop.infrastructure.notify import StderrNotifier


def test_build_runner_wires_no_probe_and_stderr_notifier(tmp_path: Path) -> None:
    context = build_runner(cwd=tmp_path, no_probe=True)
    assert context.runner._no_probe is True
    assert context.runner._wait_policy.no_probe is True
    assert isinstance(context.runner._notifier, StderrNotifier)
    assert isinstance(context.runner._control, FileRunControl)


def test_build_runner_strict_autonomy_disables_ask_question(tmp_path: Path) -> None:
    source = inspect.getsource(build_runner)
    assert "del strict_autonomy" not in source
    context = build_runner(cwd=tmp_path, strict_autonomy=True)
    assert isinstance(context.gateway, AntigravityAgentGateway)
    cfg = context.gateway._config()
    assert BuiltinTools.ASK_QUESTION in (cfg.capabilities.disabled_tools or [])
