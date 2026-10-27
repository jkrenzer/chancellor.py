"""Placeholder CLI app; real subcommands arrive with the source migration."""

from typing import Annotated

import typer

from chancellor import __version__

app = typer.Typer(add_completion=False)


def _show_version(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_show_version,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = False,
) -> None:
    """Placeholder command group for Chancellor."""
    del version
