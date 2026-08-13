"""Domain-level error hierarchy. Pure — carries no I/O state."""

from __future__ import annotations


class AgyloopError(Exception):
    """Base class for every error raised by agyloop's own logic."""


class BudgetExceededError(AgyloopError):
    """Raised when a run exceeds its configured turn, token, or estimate budget."""


class AuthenticationFailedError(AgyloopError):
    """Raised when the agent gateway reports a terminal authentication failure.

    Never retryable — the run loop must abort rather than wait.
    """
