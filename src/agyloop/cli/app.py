"""Typer application and console-script entry point."""

from typing import Annotated

import typer

from agyloop import __version__

app = typer.Typer(
    name="agyloop",
    help="Autonomous Google Antigravity and Gemini session runner.",
    add_completion=False,
    no_args_is_help=True,
)


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
