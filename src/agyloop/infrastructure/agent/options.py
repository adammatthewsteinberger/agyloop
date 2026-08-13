"""Build ``LocalAgentConfig`` for unattended Antigravity SDK sessions.

Additive ``system_instructions`` only — never ``CustomSystemInstructions``
(F5.2). Policies always include ``allow_all()`` plus workspace/destructive
scopes unless the permission mode is ``yolo``.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from google.antigravity import LocalAgentConfig
from google.antigravity.types import (
    BuiltinTools,
    CapabilitiesConfig,
    SystemInstructionSection,
    TemplatedSystemInstructions,
)

from agyloop.domain.permission import (
    DEFAULT_USER_PERMISSION_MODE,
    UserPermissionMode,
)
from agyloop.infrastructure.agent.autonomy import (
    AUTONOMY_SYSTEM_PROMPT_FRAGMENT,
    autonomy_hooks,
    build_autonomy_policies,
)


def _additive_system_instructions(system_prompt_append: str = "") -> TemplatedSystemInstructions:
    content = AUTONOMY_SYSTEM_PROMPT_FRAGMENT
    extra = system_prompt_append.strip()
    if extra:
        content = f"{content}\n\n{extra}"
    return TemplatedSystemInstructions(
        sections=[SystemInstructionSection(content=content, title="agyloop_autonomy")]
    )


def _capabilities_for(permission_mode: UserPermissionMode) -> CapabilitiesConfig:
    if permission_mode == "safe":
        return CapabilitiesConfig(enabled_tools=BuiltinTools.nondestructive())
    return CapabilitiesConfig()


def build_local_config(
    *,
    cwd: str,
    conversation_id: str | None = None,
    model: str | None = None,
    permission_mode: UserPermissionMode = DEFAULT_USER_PERMISSION_MODE,
    add_dirs: Sequence[str] | None = None,
    system_prompt_append: str = "",
    api_key: str | None = None,
) -> LocalAgentConfig:
    """Construct a headless, autonomous ``LocalAgentConfig``.

    Does not require ``GOOGLE_API_KEY`` at construction time; the SDK reads
    credentials when the Agent session starts.
    """
    workspace = str(Path(cwd).resolve())
    extra_dirs = [str(Path(path).resolve()) for path in (add_dirs or ())]
    return LocalAgentConfig(
        system_instructions=_additive_system_instructions(system_prompt_append),
        capabilities=_capabilities_for(permission_mode),
        policies=build_autonomy_policies(
            cwd=workspace,
            add_dirs=extra_dirs,
            permission_mode=permission_mode,
        ),
        hooks=autonomy_hooks(),
        workspaces=[workspace, *extra_dirs],
        conversation_id=conversation_id,
        model=model,
        api_key=api_key,
    )
