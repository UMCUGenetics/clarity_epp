import typer

import clarity_epp.export

app = typer.Typer(no_args_is_help=True)
app.add_typer(clarity_epp.export.app, name="export")


def main() -> None:
    app()
