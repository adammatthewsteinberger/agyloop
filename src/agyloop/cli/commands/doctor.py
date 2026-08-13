from __future__ import annotations

from pathlib import Path

import typer

from agyloop import bootstrap
from agyloop.application.usecases.doctor import all_passed, run_doctor
from agyloop.cli.render import render_doctor_checks

app = typer.Typer(add_completion=False)


@app.callback(invoke_without_command=True)
def doctor(ctx: typer.Context) -> None:
    """Pre-flight checks: resolve GOOGLE_API_KEY or ADC auth lane and source.

    Reports the effective Gemini lane without guessing. Asserts no interactive
    hooks. Does not read live quota — check AI Studio for that.
    """
    if ctx.invoked_subcommand is not None:
        return
    env = bootstrap.build_doctor_environment()
    checks = run_doctor(env, cwd=Path.cwd())
    typer.echo(render_doctor_checks(checks))
    if not all_passed(checks):
        raise typer.Exit(code=1)
