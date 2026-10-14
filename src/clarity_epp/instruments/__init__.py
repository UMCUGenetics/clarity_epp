"""Collection of instruments supported by the Clarity EPP application.

Often, each instrument has its own set of methods for interacting with it.
These methods are grouped together in a typer cli named after the instrument.
"""

import typer

from . import tecan

cli = typer.Typer(no_args_is_help=True)
cli.add_typer(tecan.cli, name="tecan")
