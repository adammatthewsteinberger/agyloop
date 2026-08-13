"""Throwaway capacity probe: cheapest ``chat()``, no ``conversation_id`` (F12).

A rejected probe may still consume RPD, so the runner counts it in the budget
ledger. ``--no-probe`` skips this adapter entirely.
"""

from __future__ import annotations

from pathlib import Path

from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.types import (
    AntigravityCancelledError,
    AntigravityConnectionError,
    AntigravityExecutionError,
    AntigravityValidationError,
    BuiltinTools,
    CapabilitiesConfig,
    ChatResponse,
)

from agyloop.application.dto import TurnOutcome
from agyloop.domain.classify import TurnSignals
from agyloop.domain.errors import AgentConfigError
from agyloop.infrastructure.agent.autonomy import autonomy_hooks, build_autonomy_policies
from agyloop.infrastructure.agent.translate import (
    outcome_from_exception,
    partial_text_from_response,
    verdict_from_structured,
)

PROBE_PROMPT = "Reply with the single word OK and nothing else."


def build_probe_config(
    *,
    cwd: str,
    model: str | None = None,
    api_key: str | None = None,
) -> LocalAgentConfig:
    workspace = str(Path(cwd).resolve())
    return LocalAgentConfig(
        system_instructions=PROBE_PROMPT,
        capabilities=CapabilitiesConfig(enabled_tools=BuiltinTools.none()),
        policies=build_autonomy_policies(cwd=workspace, permission_mode="autonomous"),
        hooks=autonomy_hooks(),
        workspaces=[workspace],
        conversation_id=None,
        model=model,
        api_key=api_key,
        mcp_servers=[],
    )


class AntigravityCapacityProbe:
    """One-shot throwaway Agent used only to re-check capacity."""

    def __init__(
        self,
        *,
        cwd: str,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self._cwd = cwd
        self._model = model
        self._api_key = api_key

    def set_model(self, model: str | None) -> None:
        self._model = model

    async def probe(self) -> TurnOutcome:
        agent = Agent(build_probe_config(cwd=self._cwd, model=self._model, api_key=self._api_key))
        session = await agent.__aenter__()
        response: ChatResponse | None = None
        try:
            response = await session.chat(PROBE_PROMPT)
            output_text = await response.text()
            structured = await response.structured_output()
            return TurnOutcome(
                signals=TurnSignals(),
                verdict=verdict_from_structured(structured),
                output_text=output_text,
                session_id=None,
            )
        except AntigravityValidationError as exc:
            raise AgentConfigError(str(exc)) from exc
        except (
            AntigravityCancelledError,
            AntigravityExecutionError,
            AntigravityConnectionError,
        ) as exc:
            partial = partial_text_from_response(response) if response is not None else ""
            return outcome_from_exception(exc, output_text=partial, session_id=None)
        finally:
            await agent.__aexit__(None, None, None)
