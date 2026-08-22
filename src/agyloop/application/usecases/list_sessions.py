# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Use case: list agyloop's local run registry (not vendor conversations)."""

from __future__ import annotations

from agyloop.application.ports import SessionCatalog
from agyloop.domain.session import SessionRef


def list_sessions(catalog: SessionCatalog, cwd: str | None = None) -> list[SessionRef]:
    return catalog.list_all(cwd)
