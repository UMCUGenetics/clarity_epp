"""Configure command line arguments using Typer by defining nested/grouped subcommands."""

import typer

from clarity_epp import actions, instruments

cli = typer.Typer(no_args_is_help=True)
cli.add_typer(actions.cli, name="actions")
cli.add_typer(instruments.cli, name="instruments")
