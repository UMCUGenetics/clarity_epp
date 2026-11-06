import typer

from . import label_printer, tecan

cli = typer.Typer(no_args_is_help=True)
cli.add_typer(tecan.cli, name="tecan")
cli.add_typer(label_printer.cli, name="label_printer")
