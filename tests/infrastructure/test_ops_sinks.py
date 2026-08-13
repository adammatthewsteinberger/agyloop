from pathlib import Path

import pytest

from agyloop.infrastructure.config import load_config
from agyloop.infrastructure.events import JsonlRunEventSink
from agyloop.infrastructure.state_bus import FileStateBus


def test_load_config_nested_toml_and_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "agyloop.toml").write_text(
        "[model]\nlow = 'g-low'\nmedium = 'g-med'\nhigh = 'g-high'\n[run]\nmax_turns = 7\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("AGYLOOP_MAX_TURNS", raising=False)
    cfg = load_config(cwd=tmp_path, home=tmp_path)
    assert cfg.model_low == "g-low"
    assert cfg.model_high == "g-high"
    assert cfg.max_turns == 7
    monkeypatch.setenv("AGYLOOP_MAX_TURNS", "11")
    cfg = load_config(cwd=tmp_path, home=tmp_path)
    assert cfg.max_turns == 11
    cfg = load_config(cwd=tmp_path, home=tmp_path, cli_overrides={"max_turns": 3})
    assert cfg.max_turns == 3


def test_event_sink_redacts_and_binds(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    sink = JsonlRunEventSink(path, run_id="r1", trace_id="t1")
    sink.bind(session_id="s1", attempt=2, phase="RUNNING")
    sink.emit("turn.completed", {"api_key": "secret", "ok": True})
    line = path.read_text(encoding="utf-8").strip()
    assert "secret" not in line
    assert "***" in line
    assert "turn.completed" in line


def test_state_bus_writes_status_and_bus(tmp_path: Path) -> None:
    bus = FileStateBus(
        status_path=tmp_path / "status.json",
        bus_path=tmp_path / "bus.jsonl",
        run_id="r1",
    )
    bus.publish("status", {"phase": "RUNNING", "access_token": "sekrit-token"})
    status = (tmp_path / "status.json").read_text(encoding="utf-8")
    assert "RUNNING" in status
    assert "sekrit-token" not in status
    assert "***" in status
    assert (tmp_path / "bus.jsonl").read_text(encoding="utf-8").count("\n") == 1
