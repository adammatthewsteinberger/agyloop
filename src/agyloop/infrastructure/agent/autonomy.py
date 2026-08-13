"""Never-block-on-a-human guarantees for the Antigravity SDK path.

See docs/plans/architecture-and-roadmap.md §8 and research-notes.md F2, F5:
``policy.allow_all()`` is the autonomy switch; ``ask_question`` is denied with
guidance (never auto-answered); interactive hooks are never registered.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

from google.antigravity.hooks.hooks import HookContext, PreToolCallDecideHook
from google.antigravity.hooks.policy import Policy, allow_all, deny, workspace_only
from google.antigravity.types import BuiltinTools, HookResult, ToolCall

from agyloop.domain.permission import UserPermissionMode

ASK_QUESTION_DENY_MESSAGE = (
    "Running autonomously — no human is available to answer. Choose the option you "
    "would recommend, state the assumption you are making in your next message, "
    "and proceed. Do not call `ask_question` again for this decision."
)

AUTONOMY_SYSTEM_PROMPT_FRAGMENT = (
    "You are running autonomously and unattended. Nobody is watching this "
    "session in real time and nobody can answer a question mid-task. Never end "
    "a turn by asking 'Shall I proceed?' or waiting for confirmation on a "
    "reversible action that follows from the task — just do it. If you would "
    "normally ask a clarifying question, make the most reasonable assumption, "
    "state it plainly, and continue. "
    "Structured completion verdict: leave blocked_on null unless a human or "
    "external dependency must intervene. Waiting on a background task, test "
    "suite, or build you started belongs in remaining_work with blocked_on "
    "null — a non-null blocked_on stops this autonomous run permanently."
)

_DESTRUCTIVE_COMMAND = re.compile(
    r"(?:"
    r"\brm\s+-[a-zA-Z]*[rf][a-zA-Z]*[rf]\b"
    r"|\bmkfs(?:\.\w+)?\b"
    r"|\bdd\s+if="
    r"|\b(?:shutdown|reboot|halt|poweroff)\b"
    r")",
    re.IGNORECASE,
)

_ASK_QUESTION_NAMES = frozenset(
    {BuiltinTools.ASK_QUESTION.value, BuiltinTools.ASK_QUESTION.name, "ask_question"}
)


def _tool_name(data: object) -> str:
    name = getattr(data, "name", "")
    value = getattr(name, "value", None)
    if isinstance(value, str):
        return value
    return str(name)


class DenyAskQuestionHook(PreToolCallDecideHook):  # type: ignore[misc]
    """Decide hook: deny ``ask_question`` with guidance, allow every other tool.

    ``run`` is async because that is the SDK hook contract. The body is
    synchronous — it must never wait on a human. ``misc`` ignore: the SDK
    ships without ``py.typed``, so the base hook class is ``Any`` under mypy.
    """

    async def run(self, context: HookContext, data: ToolCall) -> HookResult:
        del context
        if _tool_name(data) in _ASK_QUESTION_NAMES:
            return HookResult(allow=False, message=ASK_QUESTION_DENY_MESSAGE)
        return HookResult(allow=True)


def _command_line_from_args(args: dict[str, object]) -> str:
    for key in ("CommandLine", "command_line", "command", "Command"):
        value = args.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _is_destructive_command(args: dict[str, object]) -> bool:
    return _DESTRUCTIVE_COMMAND.search(_command_line_from_args(args)) is not None


def destructive_command_denies() -> list[Policy]:
    return [
        deny(
            BuiltinTools.RUN_COMMAND.value,
            when=_is_destructive_command,
            name="deny_destructive_commands",
        )
    ]


def autonomy_hooks() -> list[PreToolCallDecideHook]:
    return [DenyAskQuestionHook()]


def build_autonomy_policies(
    *,
    cwd: str,
    add_dirs: Sequence[str] | None = None,
    permission_mode: UserPermissionMode = "autonomous",
) -> list[Policy | list[Policy]]:
    """Compile the agyloop permission mode into an SDK policy list.

    ``yolo`` drops workspace and destructive scopes. ``--yolo`` is a later CLI
    flag; the gateway already understands the mode so the adapter is ready.
    """
    policies: list[Policy | list[Policy]] = [allow_all()]
    if permission_mode == "yolo":
        return policies
    workspaces = [str(Path(cwd).resolve()), *(str(Path(p).resolve()) for p in (add_dirs or ()))]
    policies.append(workspace_only(workspaces))
    policies.extend(destructive_command_denies())
    return policies
