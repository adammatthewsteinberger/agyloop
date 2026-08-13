"""A0b/A0c harness path selection, copy-patch, monkeypatch restore, backups."""

from __future__ import annotations

import types
from pathlib import Path

import pytest

from agyloop.domain.classify import WITHDRAWN_INPUT_DETECTION_MODEL
from agyloop.infrastructure.agent.harness_retarget import (
    BACKUP_SUFFIX,
    HARNESS_PATH_ENV,
    INPUT_DETECTION_BINARY_ID,
    apply_binary_path_monkeypatch,
    binary_contains_withdrawn,
    overwrite_site_packages_harness,
    patch_harness_bytes,
    prepare_harness,
    restore_harness,
    restore_site_packages_backup,
    restore_site_packages_backups,
    select_harness_path,
    write_patched_copy,
)

_STOCK = b"hdr\0" + WITHDRAWN_INPUT_DETECTION_MODEL.encode("ascii") + b"\0tail"


def test_patch_harness_bytes_same_length_live_id() -> None:
    patched = patch_harness_bytes(_STOCK)
    assert WITHDRAWN_INPUT_DETECTION_MODEL.encode("ascii") not in patched
    assert INPUT_DETECTION_BINARY_ID.encode("ascii") in patched
    assert len(patched) == len(_STOCK)


def test_select_harness_path_honors_operator(tmp_path: Path) -> None:
    patched = tmp_path / "patched"
    patched.write_bytes(b"x")
    assert select_harness_path(operator_path="/opt/custom", patched=patched) == "/opt/custom"
    assert select_harness_path(operator_path=None, patched=patched) == str(patched)
    assert select_harness_path(operator_path=None, patched=None) is None


def test_prepare_harness_does_not_override_preset_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AGYLOOP_SKIP_HARNESS_RETARGET", "0")
    monkeypatch.setenv(HARNESS_PATH_ENV, "/already/set")
    monkeypatch.setenv("AGYLOOP_HARNESS_CACHE", str(tmp_path / "cache"))
    session = prepare_harness(enable_proxy_if_needed=False)
    try:
        assert os_env_harness() == "/already/set"
        assert "operator_harness_path" in session.notes
    finally:
        restore_harness()
        monkeypatch.setenv(HARNESS_PATH_ENV, "/already/set")


def os_env_harness() -> str | None:
    import os

    return os.environ.get(HARNESS_PATH_ENV)


def test_prepare_harness_copy_patch_sets_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import os

    stock = tmp_path / "localharness"
    stock.write_bytes(_STOCK)
    stock.chmod(0o755)
    cache = tmp_path / "cache"
    monkeypatch.setenv("AGYLOOP_SKIP_HARNESS_RETARGET", "0")
    monkeypatch.delenv(HARNESS_PATH_ENV, raising=False)
    monkeypatch.setenv("AGYLOOP_HARNESS_CACHE", str(cache))
    monkeypatch.setenv("AGYLOOP_NO_SITE_PACKAGES_PATCH", "1")
    monkeypatch.setattr(
        "agyloop.infrastructure.agent.harness_retarget.stock_harness_path",
        lambda: stock,
    )
    session = prepare_harness(enable_proxy_if_needed=False)
    try:
        assert session.patched_binary is not None
        assert os.environ[HARNESS_PATH_ENV] == str(session.patched_binary)
        assert not binary_contains_withdrawn(session.patched_binary)
        assert "copy_patch" in session.notes
    finally:
        restore_harness()


def test_write_patched_copy_roundtrip(tmp_path: Path) -> None:
    stock = tmp_path / "localharness"
    stock.write_bytes(_STOCK)
    dest = tmp_path / "out" / "localharness"
    write_patched_copy(stock, dest)
    assert dest.is_file()
    assert not binary_contains_withdrawn(dest)


def test_monkeypatch_restores_stub_module(tmp_path: Path) -> None:
    stub = types.SimpleNamespace(_get_default_binary_path_external=lambda: "/stock")
    patched = tmp_path / "patched"
    patched.write_bytes(b"ok")
    restore = apply_binary_path_monkeypatch(stub, patched_binary=patched)
    assert stub._get_default_binary_path_external() == str(patched)
    restore()
    assert stub._get_default_binary_path_external() == "/stock"


def test_site_packages_backup_and_restore(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AGYLOOP_NO_SITE_PACKAGES_PATCH", raising=False)
    stock = tmp_path / "localharness"
    stock.write_bytes(_STOCK)
    backup = overwrite_site_packages_harness(stock)
    assert backup is not None
    assert backup.name.endswith(BACKUP_SUFFIX)
    assert backup.read_bytes() == _STOCK
    assert not binary_contains_withdrawn(stock)
    restore_site_packages_backup(backup)
    assert stock.read_bytes() == _STOCK
    assert not backup.is_file()


def test_repair_harness_restores_backup(tmp_path: Path) -> None:
    stock = tmp_path / "localharness"
    stock.write_bytes(INPUT_DETECTION_BINARY_ID.encode("ascii"))
    backup = tmp_path / f"localharness{BACKUP_SUFFIX}"
    backup.write_bytes(_STOCK)
    message = restore_site_packages_backups(stock)
    assert "restored" in message
    assert stock.read_bytes() == _STOCK
