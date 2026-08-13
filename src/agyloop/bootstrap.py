"""Composition root — the only module that wires infrastructure into ports.

CLI and application never import infrastructure; they ask this module.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from agyloop.application.dto import TurnOutcome
from agyloop.application.ports import AgentGateway, CapacityProbe
from agyloop.application.runner import AutonomousRunner
from agyloop.application.usecases.doctor import DoctorEnvironment
from agyloop.application.usecases.run_control import EnqueueResult, request_prompt, request_stop
from agyloop.domain.budget import Budget
from agyloop.domain.classify import TurnSignals
from agyloop.domain.errors import UnsafeSkipPermissionsError
from agyloop.domain.model_profile import resolve_profile
from agyloop.domain.permission import DEFAULT_USER_PERMISSION_MODE, parse_user_permission_mode
from agyloop.domain.plan import WorkPlan
from agyloop.domain.waiting import WaitPolicyConfig
from agyloop.infrastructure.agent.catalog import RunRegistryCatalog
from agyloop.infrastructure.agent.cli_argv import UNSAFE_SKIP_WARNING
from agyloop.infrastructure.agent.cli_argv import (
    validate_unsafe_skip_permissions as _validate_unsafe_skip_permissions,
)
from agyloop.infrastructure.agent.gateway import AntigravityAgentGateway
from agyloop.infrastructure.agent.probe import AntigravityCapacityProbe
from agyloop.infrastructure.control import FileRunControl
from agyloop.infrastructure.doctor_env import RealDoctorEnvironment
from agyloop.infrastructure.notify import StderrNotifier
from agyloop.infrastructure.rundir import (
    RunDirectory,
    list_run_directories,
    resolve_run_directory,
    runs_root_for,
)


@dataclass(frozen=True, slots=True)
class RunnerContext:
    runner: AutonomousRunner
    gateway: AgentGateway
    run_dir: RunDirectory
    run_id: str
    trace_id: str


class _SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class _AsyncioSleeper:
    async def sleep_until(self, instant: datetime) -> None:
        delay = (instant - datetime.now(UTC)).total_seconds()
        if delay > 0:
            await asyncio.sleep(delay)


class _NullAuditLog:
    def record(self, event_type: str, payload: dict[str, Any]) -> None:
        del event_type, payload


class _StderrProgress:
    def turn_sent(self, *, attempt: int) -> None:
        del attempt

    def waiting(self, *, reason: str, until: datetime) -> None:
        del reason, until

    def finished(self, *, success: bool, reason: str) -> None:
        del success, reason


class _NoOpCapacityProbe:
    """Safety dummy for ``--no-probe``: if probe() is called, issue zero chat()."""

    async def probe(self) -> TurnOutcome:
        return TurnOutcome(signals=TurnSignals(), verdict=None, output_text="", session_id=None)


def _run_directory_for_conversation(cwd: Path, conversation_id: str | None) -> RunDirectory | None:
    if not conversation_id:
        return None
    for directory in list_run_directories(cwd):
        meta = directory.read_meta()
        if meta.conversation_id == conversation_id or meta.run_id == conversation_id:
            return directory
    return None


def _plan_seed_from_registry(cwd: Path, conversation_id: str | None) -> str | None:
    directory = _run_directory_for_conversation(cwd, conversation_id)
    return directory.read_plan_text() if directory is not None else None


def build_runner(
    *,
    cwd: Path,
    plan: WorkPlan | None = None,
    plan_path: Path | None = None,
    conversation_id: str | None = None,
    plan_seed: str | None = None,
    model: str | None = None,
    max_turns: int | None = None,
    max_wait_seconds: float | None = None,
    max_tokens: int | None = None,
    no_probe: bool = False,
    strict_autonomy: bool = False,
    permission_mode: str = DEFAULT_USER_PERMISSION_MODE,
    resume: bool = False,
) -> RunnerContext:
    del strict_autonomy
    run_dir = _run_directory_for_conversation(cwd, conversation_id) if resume else None
    if run_dir is None:
        run_dir = RunDirectory.create(runs_root_for(cwd), cwd=cwd, plan_path=plan_path)
    run_id = run_dir.read_meta().run_id
    trace_id = str(uuid.uuid4())
    parsed_mode = parse_user_permission_mode(permission_mode)
    seed = plan_seed or _plan_seed_from_registry(cwd, conversation_id)
    if seed is None and plan is not None:
        seed = plan.raw_text
    gateway = AntigravityAgentGateway(
        cwd=str(cwd),
        conversation_id=conversation_id,
        model=model,
        permission_mode=parsed_mode,
        plan_seed=seed,
    )
    probe: CapacityProbe
    if no_probe:
        probe = _NoOpCapacityProbe()
    else:
        probe = AntigravityCapacityProbe(cwd=str(cwd), model=model)
    wait_policy = WaitPolicyConfig(
        max_wait=timedelta(seconds=max_wait_seconds) if max_wait_seconds else None,
        no_probe=no_probe,
    )
    profile = resolve_profile(model=model)
    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=probe,
        clock=_SystemClock(),
        sleeper=_AsyncioSleeper(),
        audit_log=_NullAuditLog(),
        progress=_StderrProgress(),
        budget=Budget(max_turns=max_turns, max_tokens=max_tokens),
        wait_policy=wait_policy,
        run_id=run_id,
        plan=plan,
        meta_updater=run_dir.update_meta,
        trace_id=trace_id,
        profile=profile,
        permission_mode=parsed_mode,
        notifier=StderrNotifier(),
        no_probe=no_probe,
        run_control=FileRunControl(run_dir.inbox),
    )
    return RunnerContext(
        runner=runner,
        gateway=gateway,
        run_dir=run_dir,
        run_id=run_id,
        trace_id=trace_id,
    )


def build_session_catalog() -> RunRegistryCatalog:
    return RunRegistryCatalog()


def build_doctor_environment() -> DoctorEnvironment:
    return RealDoctorEnvironment()


def enqueue_stop(cwd: Path, run_id: str | None = None) -> EnqueueResult:
    directory = resolve_run_directory(cwd, run_id)
    inbox = FileRunControl(directory.inbox)
    return request_stop(inbox, run_id=directory.read_meta().run_id)


def enqueue_prompt(
    cwd: Path,
    text: str,
    *,
    immediate: bool,
    run_id: str | None = None,
) -> EnqueueResult:
    directory = resolve_run_directory(cwd, run_id)
    inbox = FileRunControl(directory.inbox)
    return request_prompt(inbox, text, immediate=immediate, run_id=directory.read_meta().run_id)


def validate_unsafe_skip_permissions(cwd: Path, *, sandbox: bool = False) -> None:
    """Refuse ``--unsafe-skip-permissions`` under root / sandbox / non-git cwd."""
    _validate_unsafe_skip_permissions(cwd=cwd, sandbox=sandbox)


def refuse_unsafe_skip_on_sdk_path(cwd: Path) -> None:
    """Gate then fail closed: SDK ``run`` never honors skip-permissions."""
    validate_unsafe_skip_permissions(cwd)
    raise UnsafeSkipPermissionsError(
        "--unsafe-skip-permissions is for the CLI adapter argv builder "
        "(build_agy_argv), not the SDK gateway. The SDK path uses policies / "
        "--yolo for autonomy scope and never emits --dangerously-skip-permissions. "
        f"{UNSAFE_SKIP_WARNING}"
    )
