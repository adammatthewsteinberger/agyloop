"""Completion verdicts — was the whole task finished, or just this turn?

Primary source is the structured-output verdict the model returns per turn.
A substring marker is retained as a fallback when structured output is absent.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_DONE_MARKER = "AGYLOOP_TASK_FULLY_COMPLETE"

DONE_MARKER_INSTRUCTION = (
    f"When the entire task is fully complete, include the exact token "
    f"{DEFAULT_DONE_MARKER} in your final message. This marker is mandatory "
    f"even when you also emit structured output; if structured output is "
    f"unavailable it is the completion signal. Never treat a missing verdict "
    f"as completion."
)

COMPLETION_RESPONSE_SCHEMA: dict[str, object] = {
    "type": "object",
    "title": "AgyloopCompletionVerdict",
    "description": (
        "Structured completion verdict for an unattended run. "
        "blocked_on outranks complete. A missing verdict is never completion."
    ),
    "properties": {
        "complete": {
            "type": "boolean",
            "description": "True only when the entire task is finished.",
        },
        "remaining_work": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Work still to do. Waitable self-started work belongs here.",
        },
        "blocked_on": {
            "type": ["string", "null"],
            "description": (
                "Non-null only for a true external or human blocker. "
                "A non-null value stops the autonomous run permanently."
            ),
        },
        "summary": {
            "type": "string",
            "description": "Short summary of what this turn accomplished.",
        },
    },
    "required": ["complete", "remaining_work", "blocked_on", "summary"],
    "additionalProperties": False,
}


@dataclass(frozen=True, slots=True)
class Done:
    summary: str = ""


@dataclass(frozen=True, slots=True)
class Continue:
    remaining_work: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Blocked:
    reason: str


CompletionVerdict = Done | Continue | Blocked


@dataclass(frozen=True, slots=True)
class StructuredVerdict:
    """Mirrors the JSON schema handed to the model:
    {"complete": bool, "remaining_work": [str], "blocked_on": str|null, "summary": str}

    ``blocked_on`` outranks ``complete``. It is only for true external/human
    blockers; waitable self-started work belongs in ``remaining_work``.
    """

    complete: bool
    remaining_work: tuple[str, ...] = ()
    blocked_on: str | None = None
    summary: str = ""


def evaluate(
    *,
    structured: StructuredVerdict | None,
    output_text: str,
    done_marker: str = DEFAULT_DONE_MARKER,
    cost_usd: float = 0.0,
    empty_turn_streak: int = 0,
    empty_turn_limit: int = 3,
) -> CompletionVerdict:
    """Decide what a single turn's outcome means for the overall task.

    Precedence: a structured verdict is authoritative when present. Only when it
    is absent do we fall back to substring-matching the done marker in raw text.
    A missing verdict is never Done.
    """
    if structured is not None:
        if structured.blocked_on:
            return Blocked(reason=structured.blocked_on)
        if structured.complete:
            return Done(summary=structured.summary)
        return Continue(remaining_work=structured.remaining_work)

    if done_marker in output_text:
        return Done(summary="")

    if not output_text.strip() and cost_usd <= 0.0:
        if empty_turn_streak + 1 >= empty_turn_limit:
            return Blocked(reason="repeated empty model responses")
        return Continue(
            remaining_work=("Waiting for a non-empty model response",),
        )

    return Continue(remaining_work=())
