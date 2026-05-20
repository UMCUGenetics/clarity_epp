import typer

import clarity_epp.instruments

cli = typer.Typer(no_args_is_help=True)
cli.add_typer(clarity_epp.instruments.cli, name="instruments")
