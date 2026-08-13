"""Autonomy switch for LocalAgentConfig — never block on a human."""

from __future__ import annotations

from google.antigravity.hooks import policy
from google.antigravity.types import CustomSystemInstructions
from google.antigravity.utils.interactive import AskQuestionHook, ToolConfirmationHook

from agyloop.infrastructure.agent.options import build_local_config
from agyloop.infrastructure.agent.policies import (
    config_has_allow_all,
    config_has_nonblocking_policies,
)


def test_local_config_is_autonomous():
    cfg = build_local_config(cwd=".")
    assert config_has_allow_all(cfg) or config_has_nonblocking_policies(cfg)


def test_local_config_attaches_allow_all() -> None:
    cfg = build_local_config(cwd=".")
    assert config_has_allow_all(cfg)
    assert any(p.name == "allow_all" for p in cfg.policies)


def test_local_config_never_uses_ask_user_blocking_handler() -> None:
    cfg = build_local_config(cwd=".")
    assert config_has_nonblocking_policies(cfg)
    for item in cfg.policies:
        assert item.decision != policy.Decision.ASK_USER


def test_local_config_never_registers_interactive_hooks() -> None:
    cfg = build_local_config(cwd=".")
    for hook in cfg.hooks:
        assert not isinstance(hook, (ToolConfirmationHook, AskQuestionHook))
        assert "utils.interactive" not in type(hook).__module__


def test_local_config_uses_additive_system_instructions() -> None:
    cfg = build_local_config(cwd=".")
    assert not isinstance(cfg.system_instructions, CustomSystemInstructions)
    normalized = cfg._get_system_instructions()
    assert normalized is not None
    assert not isinstance(normalized, CustomSystemInstructions)


def test_local_config_scopes_workspace_and_denies_destructive_commands() -> None:
    cfg = build_local_config(cwd=".")
    names = {p.name for p in cfg.policies}
    assert "workspace_only" in names
    assert any("destructive" in (p.name or "") for p in cfg.policies)
