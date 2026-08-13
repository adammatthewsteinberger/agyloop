"""Exception and chunk translation into TurnSignals / TurnOutcome."""

from __future__ import annotations

from datetime import timedelta

from google.antigravity.types import (
    AntigravityCancelledError,
    AntigravityConnectionError,
    AntigravityExecutionError,
    AntigravityValidationError,
    Text,
    Thought,
)

from agyloop.application.dto import TurnOutcome
from agyloop.domain.capacity import Available, WindowExhausted
from agyloop.domain.classify import classify
from agyloop.domain.errors import AgentConfigError
from agyloop.infrastructure.agent.translate import (
    outcome_from_chunks,
    outcome_from_exception,
    signals_from_exception,
)


def test_execution_error_429_maps_to_turn_signals() -> None:
    exc = AntigravityExecutionError(
        "429 RESOURCE_EXHAUSTED: Resource has been exhausted (e.g. check quota)."
    )
    signals = signals_from_exception(exc)
    assert signals.exception_type == "AntigravityExecutionError"
    assert signals.http_status == 429
    assert signals.status == "RESOURCE_EXHAUSTED" or signals.google_status == "RESOURCE_EXHAUSTED"
    state = classify(signals)
    assert isinstance(state, WindowExhausted)


def test_cancelled_error_is_not_a_capacity_signal() -> None:
    exc = AntigravityCancelledError("operator stop")
    signals = signals_from_exception(exc)
    assert signals.exception_type == "AntigravityCancelledError"
    assert "cancelled" in (signals.exception_type or "").casefold()
    state = classify(signals)
    assert isinstance(state, Available)


def test_validation_error_is_our_bug() -> None:
    exc = AntigravityValidationError("bad LocalAgentConfig")
    try:
        outcome_from_exception(exc)
    except AgentConfigError as wrapped:
        assert "bad LocalAgentConfig" in str(wrapped)
        assert wrapped.__cause__ is exc
    else:
        raise AssertionError("AntigravityValidationError must not become TurnSignals")


def test_connection_error_401_maps_auth_status() -> None:
    exc = AntigravityConnectionError("401 UNAUTHENTICATED: invalid API key")
    signals = signals_from_exception(exc)
    assert signals.http_status == 401
    assert (signals.status or signals.google_status) == "UNAUTHENTICATED"


def test_retry_info_delay_is_recovered_from_message() -> None:
    exc = AntigravityExecutionError('429 RESOURCE_EXHAUSTED retryDelay: "27s" rate_limit_exceeded')
    signals = signals_from_exception(exc)
    assert signals.retry_info_delay == timedelta(seconds=27)
    assert signals.error_code == "rate_limit_exceeded"


def test_chunks_preserve_partial_text_and_thoughts() -> None:
    outcome = outcome_from_chunks(
        [Thought(step_index=0, text="planning"), Text(step_index=1, text="hello")],
        session_id="abc",
    )
    assert isinstance(outcome, TurnOutcome)
    assert outcome.output_text == "hello"
    assert outcome.session_id == "abc"
    assert outcome.signals.exception_type is None
