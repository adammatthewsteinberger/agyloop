from agyloop.domain.completion import (
    COMPLETION_RESPONSE_SCHEMA,
    DEFAULT_DONE_MARKER,
    DONE_MARKER_INSTRUCTION,
    Blocked,
    Continue,
    Done,
    StructuredVerdict,
    evaluate,
)


def test_done_marker_is_agyloop_branded() -> None:
    assert DEFAULT_DONE_MARKER == "AGYLOOP_TASK_FULLY_COMPLETE"


def test_completion_schema_names_verdict_fields() -> None:
    properties = COMPLETION_RESPONSE_SCHEMA["properties"]
    assert isinstance(properties, dict)
    assert set(properties) == {"complete", "remaining_work", "blocked_on", "summary"}
    assert DEFAULT_DONE_MARKER in DONE_MARKER_INSTRUCTION


def test_structured_complete_is_done() -> None:
    v = StructuredVerdict(complete=True, summary="all done")
    assert evaluate(structured=v, output_text="") == Done(summary="all done")


def test_structured_incomplete_is_continue_with_remaining_work() -> None:
    v = StructuredVerdict(complete=False, remaining_work=("thing a", "thing b"))
    assert evaluate(structured=v, output_text="") == Continue(remaining_work=("thing a", "thing b"))


def test_structured_blocked_outranks_complete_flag() -> None:
    v = StructuredVerdict(complete=True, blocked_on="waiting on MCP auth")
    assert evaluate(structured=v, output_text="") == Blocked(reason="waiting on MCP auth")


def test_structured_empty_blocked_on_outranks_complete_flag() -> None:
    v = StructuredVerdict(complete=True, blocked_on="")
    assert evaluate(structured=v, output_text="") == Blocked(reason="")


def test_structured_incomplete_outranks_marker_in_text() -> None:
    v = StructuredVerdict(complete=False, remaining_work=("still going",))
    result = evaluate(structured=v, output_text="AGYLOOP_TASK_FULLY_COMPLETE")
    assert result == Continue(remaining_work=("still going",))


def test_fallback_marker_present_is_done() -> None:
    result = evaluate(structured=None, output_text="...\nAGYLOOP_TASK_FULLY_COMPLETE\n")
    assert result == Done(summary="")


def test_fallback_marker_absent_is_continue_never_done() -> None:
    result = evaluate(structured=None, output_text="still working on it")
    assert result == Continue(remaining_work=())
    assert not isinstance(result, Done)


def test_missing_verdict_is_continue_never_done() -> None:
    result = evaluate(structured=None, output_text="")
    assert isinstance(result, Continue)
    assert not isinstance(result, Done)


def test_fallback_uses_custom_marker() -> None:
    result = evaluate(structured=None, output_text="XYZ_DONE", done_marker="XYZ_DONE")
    assert result == Done(summary="")


def test_empty_turn_soft_continue_then_blocked() -> None:
    first = evaluate(structured=None, output_text="", cost_usd=0.0, empty_turn_streak=0)
    assert isinstance(first, Continue)
    third = evaluate(structured=None, output_text="", cost_usd=0.0, empty_turn_streak=2)
    assert isinstance(third, Blocked)
