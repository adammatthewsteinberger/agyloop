"""Typer application and console-script entry point."""

from pathlib import Path
from typing import Annotated

import typer

from agyloop import __version__, bootstrap
from agyloop.cli.commands.attach_cmd import attach, unattach
from agyloop.cli.commands.config_cmd import config_cmd
from agyloop.cli.commands.doctor import app as doctor_app
from agyloop.cli.commands.logs import logs
from agyloop.cli.commands.model_cmd import model_cmd
from agyloop.cli.commands.preset_cmd import preset_cmd
from agyloop.cli.commands.prompt import prompt
from agyloop.cli.commands.reset import reset
from agyloop.cli.commands.resume import resume
from agyloop.cli.commands.run import run
from agyloop.cli.commands.runs import app as runs_app
from agyloop.cli.commands.savepoints import app as savepoints_app
from agyloop.cli.commands.sessions import app as sessions_app
from agyloop.cli.commands.snapshot_cmd import snapshot
from agyloop.cli.commands.status import status
from agyloop.cli.commands.stop import stop
from agyloop.cli.commands.unwind import unwind
from agyloop.cli.commands.watch import watch

app = typer.Typer(
    name="agyloop",
    help=(
        "Autonomous Google Antigravity and Gemini session runner. "
        "Generated Gemini REST is `agyloop api` (ADR 0015)."
    ),
    add_completion=False,
    no_args_is_help=True,
)

app.command(name="run")(run)
app.command(name="resume")(resume)
app.command(name="stop")(stop)
app.command(name="prompt")(prompt)
app.command(name="status")(status)
app.command(name="logs")(logs)
app.command(name="watch")(watch)
app.command(name="reset")(reset)
app.command(name="model")(model_cmd)
app.command(name="preset")(preset_cmd)
app.command(name="attach")(attach)
app.command(name="unattach")(unattach)
app.command(name="config")(config_cmd)
app.command(name="snapshot")(snapshot)
app.command(name="unwind")(unwind)
app.add_typer(sessions_app, name="sessions")
app.add_typer(runs_app, name="runs")
app.add_typer(doctor_app, name="doctor")
app.add_typer(savepoints_app, name="savepoints")
app.add_typer(bootstrap.build_api_click_group(), name="api")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"agyloop {__version__}")
        raise typer.Exit()


@app.callback()
def root(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the installed agyloop version and exit.",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("-v", "--verbose", help="DEBUG-level human logs on stderr."),
    ] = False,
    log_level: Annotated[
        str | None,
        typer.Option("--log-level", help="DEBUG, INFO, WARNING, or ERROR."),
    ] = None,
    log_file: Annotated[
        Path | None,
        typer.Option("--log-file", help="Optional JSONL log file (redacted)."),
    ] = None,
) -> None:
    """Run the agyloop command-line interface."""
    del version
    level = "DEBUG" if verbose else (log_level or "INFO")
    bootstrap.configure_cli_logging(level=level, log_file=log_file)


def main() -> None:
    """Run the console application."""
    app(prog_name="agyloop")
