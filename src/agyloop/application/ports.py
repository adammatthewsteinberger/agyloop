"""Application ports — Protocols implemented by infrastructure/, never imported
from it. See docs/plans/architecture-and-roadmap.md §11: application/ knows the
SHAPE of a collaborator, never its concrete type."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from agyloop.application.dto import TurnOutcome
from agyloop.domain.control import ControlCommand
from agyloop.domain.model_profile import ModelEffortProfile
from agyloop.domain.savepoint import SavePointRef, UnwindResult
from agyloop.domain.session import SessionRef
from agyloop.domain.snapshot import SnapshotReason, SnapshotRef


class Clock(Protocol):
    def now(self) -> datetime: ...


class Sleeper(Protocol):
    async def sleep_until(self, instant: datetime) -> None: ...


class AgentGateway(Protocol):
    """Wraps a live google.antigravity Agent session. The port must not leak
    google.antigravity types: ``set_permission_mode`` takes an agyloop enum
    (autonomous | scoped | safe | yolo) that a later adapter compiles into a
    policy list. Deliberately not a one-shot query — the session survives a
    capacity rejection so the run can probe and resume.
    """

    async def send_turn(self, prompt_text: str) -> TurnOutcome: ...
    async def close(self) -> None: ...
    async def set_profile(self, profile: ModelEffortProfile) -> None: ...
    async def set_permission_mode(self, mode: str) -> None: ...
    async def set_cwd(self, cwd: str) -> None: ...
    async def set_session_resources(self, **kwargs: Any) -> None: ...
    def resolve_tool_approval(self, request_id: str, *, allow: bool, reason: str = "") -> bool: ...


class RunResources(Protocol):
    """Run-scoped attachments / skills / folders / memories applied mid-run."""

    def apply_mutate(
        self, *, action: str, kind: str, value: str, name: str | None = None
    ) -> dict[str, Any]: ...
    def gateway_payload(self) -> dict[str, Any]: ...
    def set_permission_mode(self, mode: str) -> None: ...
    def set_cwd(self, path: str) -> None: ...


class CapacityProbe(Protocol):
    async def probe(self) -> TurnOutcome: ...


class SessionCatalog(Protocol):
    """Enumerates agyloop's run registry, not vendor conversations."""

    def most_recent(self, cwd: str) -> SessionRef | None: ...
    def list_all(self, cwd: str | None = None) -> list[SessionRef]: ...


class ProgressReporter(Protocol):
    def turn_sent(self, *, attempt: int) -> None: ...
    def waiting(self, *, reason: str, until: datetime) -> None: ...
    def finished(self, *, success: bool, reason: str) -> None: ...


class AuditLog(Protocol):
    def record(self, event_type: str, payload: dict[str, Any]) -> None: ...


class Notifier(Protocol):
    def notify(self, message: str) -> None: ...


class Logger(Protocol):
    """Structured application logging — implemented by infrastructure/logging."""

    def bind(self, **kwargs: Any) -> Logger: ...
    def debug(self, event: str, **kwargs: Any) -> None: ...
    def info(self, event: str, **kwargs: Any) -> None: ...
    def warning(self, event: str, **kwargs: Any) -> None: ...
    def error(self, event: str, **kwargs: Any) -> None: ...


class RunStateStore(Protocol):
    def save(self, run_id: str, state: dict[str, Any]) -> None: ...
    def load(self, run_id: str) -> dict[str, Any] | None: ...


class SessionLock(Protocol):
    def acquire(self, session_id: str) -> bool: ...
    def release(self, session_id: str) -> None: ...


class ApiGateway(Protocol):
    """Generated Gemini REST surface (ADR 0015). ``agyloop api`` is bound from
    the committed Developer discovery baseline and guarded by a drift gate."""

    def invoke(self, method_path: str, **kwargs: Any) -> Any: ...


class RunControl(Protocol):
    def poll(self) -> list[ControlCommand]: ...


class RunEventSink(Protocol):
    def emit(self, event_type: str, payload: dict[str, Any] | None = None) -> None: ...
    def bind(
        self,
        *,
        session_id: str | None = None,
        attempt: int | None = None,
        phase: str | None = None,
        trace_id: str | None = None,
        turn_id: str | None = None,
    ) -> None: ...


class StreamUi(Protocol):
    """Optional full-screen stream UI — fed deltas; Textual lives in infrastructure."""

    def on_delta(self, text: str, *, turn_id: str, seq: int) -> None: ...
    def on_turn_boundary(self, *, turn_id: str, attempt: int) -> None: ...
    def on_prompt(self, text: str) -> None: ...
    def on_assistant(self, text: str) -> None: ...
    def on_tool(self, name: str, summary: str) -> None: ...
    def on_status(self, state: dict[str, Any]) -> None: ...
    def close(self) -> None: ...


class SavePointStore(Protocol):
    def create(
        self,
        *,
        run_id: str,
        label: str,
        message: str = "",
        attempt: int | None = None,
        verdict_name: str = "Continue",
        summary: str = "",
        remaining_work: tuple[str, ...] = (),
    ) -> SavePointRef | None: ...
    def list_points(self, run_id: str) -> list[SavePointRef]: ...
    def unwind(self, *, run_id: str, to: str, backup: bool) -> UnwindResult: ...
    def changes_since(self, since_sha: str | None) -> str: ...


class StateBus(Protocol):
    """Publish run state changes for external pollers / subscribers."""

    def publish(self, event_type: str, state: dict[str, Any]) -> None: ...


class RunSnapshotSink(Protocol):
    """Write handoff snapshots and publish path+digest on the state bus."""

    def emit(
        self,
        reason: SnapshotReason,
        *,
        context: dict[str, Any] | None = None,
        bundle: bool | None = None,
    ) -> SnapshotRef | None: ...
