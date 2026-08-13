"""Composition root wiring for adaptive wait, --no-probe, and the loud notifier."""

from pathlib import Path

from agyloop.bootstrap import build_runner
from agyloop.infrastructure.notify import StderrNotifier


def test_build_runner_wires_no_probe_and_stderr_notifier(tmp_path: Path) -> None:
    context = build_runner(cwd=tmp_path, no_probe=True)
    assert context.runner._no_probe is True
    assert context.runner._wait_policy.no_probe is True
    assert isinstance(context.runner._notifier, StderrNotifier)
