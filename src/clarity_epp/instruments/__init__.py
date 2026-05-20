import typer

from . import tecan

cli = typer.Typer(no_args_is_help=True)
cli.add_typer(tecan.cli, name="tecan")
