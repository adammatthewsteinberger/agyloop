from __future__ import annotations

import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from google.antigravity.types import ModelTarget, ModelType

from agyloop.domain.classify import WITHDRAWN_INPUT_DETECTION_MODEL
from agyloop.domain.model_profile import INPUT_DETECTION_MODEL
from agyloop.infrastructure.agent.harness_retarget import (
    BACKUP_SUFFIX,
    HarnessSession,
    _apply_sdk_monkeypatches,
    _atexit_restore,
    _build_model_targets,
    _maybe_start_proxy,
    binary_contains_withdrawn,
    cache_dir,
    overwrite_site_packages_harness,
    patch_harness_bytes,
    prepare_harness,
    restore_harness,
    restore_site_packages_backup,
    restore_site_packages_backups,
    stock_harness_path,
)


def test_build_model_targets() -> None:
    targets1 = _build_model_targets("gemini-2.5-flash", "endpoint1")
    assert len(targets1) == 2
    targets2 = _build_model_targets(INPUT_DETECTION_MODEL, "endpoint1")
    assert len(targets2) == 1


def test_cache_dir_variants(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("AGYLOOP_HARNESS_CACHE", raising=False)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg"))
    assert cache_dir() == tmp_path / "xdg" / "agyloop" / "localharness"

    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    assert "localharness" in str(cache_dir())


def test_stock_harness_path_variants(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Key error or OSError
    with patch.dict(sys.modules, {"google.antigravity.types": types.ModuleType("types")}):
        sys.modules["google.antigravity.types"].__file__ = None
        assert stock_harness_path() is None

    # Found binary
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True)
    harness = bin_dir / "localharness"
    harness.write_bytes(b"bin")
    mod = types.ModuleType("google.antigravity.types")
    mod.__file__ = str(tmp_path / "types.py")
    with patch.dict(sys.modules, {"google.antigravity.types": mod}):
        assert stock_harness_path() == harness

    # Found .exe
    harness.unlink()
    harness_exe = bin_dir / "localharness.exe"
    harness_exe.write_bytes(b"exe")
    with patch.dict(sys.modules, {"google.antigravity.types": mod}):
        assert stock_harness_path() == harness_exe


def test_binary_contains_withdrawn_error(tmp_path: Path) -> None:
    missing = tmp_path / "nonexistent"
    assert binary_contains_withdrawn(missing) is False


def test_patch_harness_bytes_unchanged() -> None:
    data = b"no withdrawn id here"
    assert patch_harness_bytes(data) == data


def test_apply_sdk_monkeypatches(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    session = HarnessSession()

    # Module cannot be imported
    with patch("importlib.import_module", side_effect=ImportError):
        with patch.dict(sys.modules, {"google.antigravity._internal.local_connection": None}, clear=False):
            sys.modules.pop("google.antigravity._internal.local_connection", None)
            _apply_sdk_monkeypatches(session, patched_binary=None)
            assert session.monkeypatch_restore is None

    # Module exists with _get_default_binary_path_external and build_models_proto
    mod = types.ModuleType("google.antigravity._internal.local_connection")
    mod._get_default_binary_path_external = lambda: "/orig/path"
    
    class FakeTarget:
        def __init__(self, name: str) -> None:
            self.name = name
        def model_copy(self, update: dict[str, str]) -> FakeTarget:
            return FakeTarget(update["name"])

    seen_models = []
    def fake_build_models(models: list[FakeTarget]) -> list[FakeTarget]:
        seen_models.extend(models)
        return models

    mod.build_models_proto = fake_build_models

    with patch.dict(sys.modules, {"google.antigravity._internal.local_connection": mod}):
        patched_file = tmp_path / "patched"
        patched_file.write_bytes(b"bin")
        _apply_sdk_monkeypatches(session, patched_binary=patched_file)
        assert mod._get_default_binary_path_external() == str(patched_file)

        # Call patched build_models_proto
        targets = [FakeTarget(f"models/{WITHDRAWN_INPUT_DETECTION_MODEL}"), FakeTarget("models/gemini-2.5-pro")]
        mod.build_models_proto(targets)
        assert seen_models[0].name == f"models/{INPUT_DETECTION_MODEL}"

        # Restore
        assert session.monkeypatch_restore is not None
        session.monkeypatch_restore()
        assert mod._get_default_binary_path_external() == "/orig/path"


def test_overwrite_site_packages_failures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGYLOOP_NO_SITE_PACKAGES_PATCH", "1")
    stock = tmp_path / "localharness"
    stock.write_bytes(b"stock")
    assert overwrite_site_packages_harness(stock) is None

    monkeypatch.delenv("AGYLOOP_NO_SITE_PACKAGES_PATCH", raising=False)
    # Patched == original
    assert overwrite_site_packages_harness(stock) is None


def test_restore_site_packages_helpers(tmp_path: Path) -> None:
    # restore_site_packages_backup on invalid path
    restore_site_packages_backup(tmp_path / "not_backup.txt")

    # restore_site_packages_backups with missing targets
    assert "no bundled localharness found" in restore_site_packages_backups(None)

    stock = tmp_path / "localharness"
    stock.write_bytes(b"live")
    assert "no backup" in restore_site_packages_backups(stock)


def test_maybe_start_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    session = HarnessSession()
    _maybe_start_proxy(session, enable=False)
    assert "proxy_disabled" in session.notes

    # Proxy OSError
    with patch("agyloop.infrastructure.agent.gemini_rewrite.GeminiRewriteProxy.start", side_effect=OSError("bind fail")):
        _maybe_start_proxy(session, enable=True)
        assert any("proxy_error" in note for note in session.notes)

    # Proxy successful start
    with patch("agyloop.infrastructure.agent.gemini_rewrite.GeminiRewriteProxy.start", return_value="http://127.0.0.1:9999"):
        _maybe_start_proxy(session, enable=True)
        assert "rewrite_proxy" in session.notes


def test_atexit_and_restore() -> None:
    restore_harness()
    _atexit_restore()


def test_prepare_harness_branch_conditions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGYLOOP_SKIP_HARNESS_RETARGET", "0")
    monkeypatch.delenv("AGYLOOP_HARNESS_PATH", raising=False)

    # 1. No stock binary
    with patch("agyloop.infrastructure.agent.harness_retarget.stock_harness_path", return_value=None):
        session = prepare_harness(enable_proxy_if_needed=False)
        assert "no_stock_binary" in session.notes
        restore_harness()

    # 2. Stock already live
    live_stock = tmp_path / "live_stock"
    live_stock.write_bytes(b"live without withdrawn")
    with patch("agyloop.infrastructure.agent.harness_retarget.stock_harness_path", return_value=live_stock):
        session = prepare_harness(enable_proxy_if_needed=False)
        assert "stock_already_live" in session.notes
        restore_harness()

    # 3. Copy patch unrunnable falls through
    withdrawn_stock = tmp_path / "withdrawn_stock"
    withdrawn_stock.write_bytes(WITHDRAWN_INPUT_DETECTION_MODEL.encode("ascii"))
    with patch("agyloop.infrastructure.agent.harness_retarget.stock_harness_path", return_value=withdrawn_stock), \
         patch("agyloop.infrastructure.agent.harness_retarget.smoke_check_harness", return_value="died"), \
         patch("agyloop.infrastructure.agent.harness_retarget.cache_dir", return_value=tmp_path / "cache"):
        session = prepare_harness(enable_proxy_if_needed=True)
        assert any("copy_patch_unrunnable" in n for n in session.notes)
        restore_harness()
