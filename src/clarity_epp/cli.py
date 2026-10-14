"""Typer CLI for the Clarity EPP application.

This module serves as the entry point for the command-line interface (CLI) of the Clarity EPP application.
The CLI is built using the Typer library. Typer simplifies CLI development by using Python type hints to automatically handle
argument parsing, validation, type conversion and help text. Compared to a large `argparse` implementation, it reduces
boilerplate, improves readability and makes commands easier to maintain as the application grows.
Its support for subcommands also helps organize complex CLIs into a clear, modular structure.
"""

import typer

import clarity_epp.instruments

cli = typer.Typer(no_args_is_help=True)
cli.add_typer(clarity_epp.instruments.cli, name="instruments")
