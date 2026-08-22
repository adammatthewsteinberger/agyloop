# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""The generated REST surface seam."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ApiGateway(Protocol):
    """Generated Gemini REST surface (ADR 0015). ``agyloop api`` is bound from
    the committed Developer discovery baseline and guarded by a drift gate."""

    def invoke(self, method_path: str, **kwargs: Any) -> Any: ...
