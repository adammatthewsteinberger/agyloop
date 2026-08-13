"""Typer application and console-script entry point."""

from typing import Annotated

import typer

from agyloop import __version__
from agyloop.cli.commands.doctor import app as doctor_app
from agyloop.cli.commands.resume import resume
from agyloop.cli.commands.run import run
from agyloop.cli.commands.sessions import app as sessions_app

app = typer.Typer(
    name="agyloop",
    help="Autonomous Google Antigravity and Gemini session runner.",
    add_completion=False,
    no_args_is_help=True,
)

app.command(name="run")(run)
app.command(name="resume")(resume)
app.add_typer(sessions_app, name="sessions")
app.add_typer(doctor_app, name="doctor")


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
