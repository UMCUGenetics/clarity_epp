import typer

from . import tecan

app = typer.Typer(no_args_is_help=True)
app.add_typer(tecan.app, name="tecan")
