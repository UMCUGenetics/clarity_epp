"""Upload functions."""

import typer

import clarity_epp.upload.samples
import clarity_epp.upload.tecan
import clarity_epp.upload.tapestation
import clarity_epp.upload.bioanalyzer
import clarity_epp.upload.magnis


app = typer.Typer(no_args_is_help=True)
app.add_typer(bioanalyzer.app, name="bioanalyzer")
app.add_typer(magnis.app, name="magnis")
app.add_typer(samples.app, name="samples")
app.add_typer(tapestation.app, name="tapestation")
app.add_typer(tecan.app, name="tecan")


if __name__ == "__main__":
    app()
