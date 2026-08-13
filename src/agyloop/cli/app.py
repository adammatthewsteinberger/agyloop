"""Typer application and console-script entry point."""

from typing import Annotated

import typer

from agyloop import __version__, bootstrap
from agyloop.cli.commands.doctor import app as doctor_app
from agyloop.cli.commands.prompt import prompt
from agyloop.cli.commands.resume import resume
from agyloop.cli.commands.run import run
from agyloop.cli.commands.savepoints import app as savepoints_app
from agyloop.cli.commands.sessions import app as sessions_app
from agyloop.cli.commands.snapshot_cmd import snapshot
from agyloop.cli.commands.stop import stop
from agyloop.cli.commands.unwind import unwind

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
app.command(name="snapshot")(snapshot)
app.command(name="unwind")(unwind)
app.add_typer(sessions_app, name="sessions")
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
) -> None:
    """Run the agyloop command-line interface."""
    del version


def main() -> None:
    """Run the console application."""
    app(prog_name="agyloop")
