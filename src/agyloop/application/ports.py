"""Backwards-compatible re-export of `application.interfaces`.

The Protocols moved into `application/interfaces/` so every seam lives in
one discoverable place, one module per collaborator family. This shim keeps
the old `from agyloop.application.ports import X` path working; new code
should import from `agyloop.application.interfaces`.
"""

from __future__ import annotations

from agyloop.application.interfaces import (
    AgentGateway,
    ApiGateway,
    AuditLog,
    AuthLane,
    AuthResolution,
    CapacityProbe,
    Clock,
    ControlInbox,
    DoctorEnvironment,
    Logger,
    Notifier,
    ProgressReporter,
    RunControl,
    RunEventSink,
    RunResources,
    RunSnapshotSink,
    RunStateStore,
    SavePointStore,
    SessionCatalog,
    SessionLock,
    Sleeper,
    StateBus,
    StreamUi,
)

__all__ = [
    "AgentGateway",
    "ApiGateway",
    "AuditLog",
    "CapacityProbe",
    "AuthLane",
    "AuthResolution",
    "Clock",
    "ControlInbox",
    "DoctorEnvironment",
    "Logger",
    "Notifier",
    "ProgressReporter",
    "RunControl",
    "RunEventSink",
    "RunResources",
    "RunSnapshotSink",
    "RunStateStore",
    "SavePointStore",
    "SessionCatalog",
    "SessionLock",
    "Sleeper",
    "StateBus",
    "StreamUi",
]
