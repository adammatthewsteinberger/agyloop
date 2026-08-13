"""CLI argv builder: never combine skip-permissions with sandbox; refuse root."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from agyloop.domain.errors import UnsafeSkipPermissionsError
from agyloop.infrastructure.agent.cli_argv import (
    ISSUE_36_URL,
    UNSAFE_SKIP_WARNING,
    build_agy_argv,
    validate_unsafe_skip_permissions,
)


def test_default_argv_uses_sandbox_and_never_emits_skip_permissions() -> None:
    invocation = build_agy_argv(prompt="hello", conversation_id="cid-1")
    argv = list(invocation.argv)
    assert "--sandbox" in argv
    assert "--dangerously-skip-permissions" not in argv
    assert "-p" in argv or "--print" in argv or "--prompt" in argv
    assert "--print-timeout" in argv
    timeout = argv[argv.index("--print-timeout") + 1]
    assert timeout != "5m0s"
    assert "--conversation" in argv
    assert "cid-1" in argv
    assert "-c" not in argv
    assert "--continue" not in argv


def test_default_settings_deny_unsandboxed() -> None:
    invocation = build_agy_argv(prompt="hello")
    assert invocation.settings["toolPermission"] == "proceed-in-sandbox"
    deny = invocation.settings["permissions"]["deny"]
    assert "unsandboxed" in deny
    assert "--dangerously-skip-permissions" not in invocation.argv


def test_unsafe_skip_permissions_omits_sandbox(tmp_path: Path) -> None:
    _init_git(tmp_path)
    invocation = build_agy_argv(
        prompt="hello",
        cwd=tmp_path,
        unsafe_skip_permissions=True,
    )
    argv = list(invocation.argv)
    assert "--dangerously-skip-permissions" in argv
    assert "--sandbox" not in argv
    assert invocation.warning == UNSAFE_SKIP_WARNING


def test_unsafe_skip_permissions_refuses_sandbox_combo(tmp_path: Path) -> None:
    _init_git(tmp_path)
    with pytest.raises(UnsafeSkipPermissionsError, match="sandbox") as exc:
        build_agy_argv(
            prompt="hello",
            cwd=tmp_path,
            sandbox=True,
            unsafe_skip_permissions=True,
        )
    assert "36" in str(exc.value) or ISSUE_36_URL in str(exc.value)


def test_unsafe_skip_permissions_refuses_root(tmp_path: Path) -> None:
    _init_git(tmp_path)
    euid = "agyloop.infrastructure.agent.cli_argv.os.geteuid"
    with patch(euid, return_value=0), pytest.raises(UnsafeSkipPermissionsError, match="root"):
        validate_unsafe_skip_permissions(cwd=tmp_path)
    with patch(euid, return_value=0), pytest.raises(UnsafeSkipPermissionsError, match="root"):
        build_agy_argv(prompt="hello", cwd=tmp_path, unsafe_skip_permissions=True)


def test_unsafe_skip_permissions_allows_non_root(tmp_path: Path) -> None:
    _init_git(tmp_path)
    with patch("agyloop.infrastructure.agent.cli_argv.os.geteuid", return_value=501):
        validate_unsafe_skip_permissions(cwd=tmp_path)
        invocation = build_agy_argv(prompt="hello", cwd=tmp_path, unsafe_skip_permissions=True)
    assert "--dangerously-skip-permissions" in invocation.argv


def test_unsafe_skip_permissions_refuses_outside_git(tmp_path: Path) -> None:
    with (
        patch("agyloop.infrastructure.agent.cli_argv.os.geteuid", return_value=501),
        pytest.raises(UnsafeSkipPermissionsError, match="git"),
    ):
        validate_unsafe_skip_permissions(cwd=tmp_path)


def test_unsafe_skip_permissions_allows_allowlisted_non_git(tmp_path: Path) -> None:
    with patch("agyloop.infrastructure.agent.cli_argv.os.geteuid", return_value=501):
        validate_unsafe_skip_permissions(cwd=tmp_path, allowlist=[str(tmp_path)])
        invocation = build_agy_argv(
            prompt="hello",
            cwd=tmp_path,
            unsafe_skip_permissions=True,
            allowlist=[str(tmp_path)],
        )
    assert "--dangerously-skip-permissions" in invocation.argv
    assert "--sandbox" not in invocation.argv


def test_unsafe_skip_warning_cites_issue_36() -> None:
    assert "36" in UNSAFE_SKIP_WARNING
    assert ISSUE_36_URL in UNSAFE_SKIP_WARNING or "antigravity-cli" in UNSAFE_SKIP_WARNING


def _init_git(repo: Path) -> None:
    (repo / ".git").mkdir()
