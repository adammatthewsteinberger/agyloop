"""Time and sleeping -- the two ambient effects the run loop needs faked."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    def now(self) -> datetime: ...


@runtime_checkable
class Sleeper(Protocol):
    async def sleep_until(self, instant: datetime) -> None: ...
