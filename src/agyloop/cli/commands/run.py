from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agyloop import bootstrap
from agyloop.application.usecases.run_plan import parse_plan_file, run_from_plan_file
from agyloop.cli.asyncio import async_command
from agyloop.domain.errors import InvalidPlanError


def run(
    plan_file: Annotated[
        Path,
        typer.Argument(
            exists=True,
            readable=True,
            help="Markdown plan file to seed a fresh Antigravity session.",
        ),
    ],
    cwd_dir: Annotated[
        Path | None,
        typer.Option(
            "--cwd",
            exists=True,
            file_okay=False,
            help="Working directory for the run (default: current directory).",
        ),
    ] = None,
    model: Annotated[str | None, typer.Option("--model", help="Gemini model id or alias.")] = None,
    max_turns: Annotated[int | None, typer.Option("--max-turns")] = None,
    max_wait_seconds: Annotated[float | None, typer.Option("--max-wait")] = None,
    max_tokens: Annotated[int | None, typer.Option("--max-tokens")] = None,
    no_probe: Annotated[
        bool,
        typer.Option(
            "--no-probe",
            help="Wait only to computed quota boundaries; issue zero probe requests.",
        ),
    ] = False,
    strict_autonomy: Annotated[bool, typer.Option("--strict-autonomy")] = False,
    safe: Annotated[bool, typer.Option("--safe", help="Nondestructive tools only.")] = False,
    yolo: Annotated[
        bool, typer.Option("--yolo", help="Drop workspace/destructive scopes.")
    ] = False,
) -> None:
    """Seed a brand-new Antigravity session from PLAN_FILE and run it unattended."""
    _run(
        plan_file=plan_file,
        cwd_dir=cwd_dir,
        model=model,
        max_turns=max_turns,
        max_wait_seconds=max_wait_seconds,
        max_tokens=max_tokens,
        no_probe=no_probe,
        strict_autonomy=strict_autonomy,
        safe=safe,
        yolo=yolo,
    )


@async_command
async def _run(
    *,
    plan_file: Path,
    cwd_dir: Path | None,
    model: str | None,
    max_turns: int | None,
    max_wait_seconds: float | None,
    max_tokens: int | None,
    no_probe: bool,
    strict_autonomy: bool,
    safe: bool,
    yolo: bool,
) -> None:
    cwd = cwd_dir.resolve() if cwd_dir is not None else Path.cwd()
    try:
        plan = parse_plan_file(plan_file)
    except InvalidPlanError as exc:
        typer.echo(f"Invalid plan file: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    permission_mode = "yolo" if yolo else ("safe" if safe else "autonomous")
    context = bootstrap.build_runner(
        cwd=cwd,
        plan=plan,
        plan_path=plan_file,
        model=model,
        max_turns=max_turns,
        max_wait_seconds=max_wait_seconds,
        max_tokens=max_tokens,
        no_probe=no_probe,
        strict_autonomy=strict_autonomy,
        permission_mode=permission_mode,
    )
    typer.echo(f"Run id: {context.run_id}", err=True)
    result = await run_from_plan_file(context.runner, plan_file)
    if not result.success:
        typer.echo(f"Run failed: {result.reason}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"Done: {result.reason}")
