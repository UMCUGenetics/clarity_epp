"""Container placement functions."""

import typer

import clarity_epp.placement.artifact
import clarity_epp.placement.barcode
import clarity_epp.placement.pipetting
import clarity_epp.placement.plate
import clarity_epp.placement.pool
import clarity_epp.placement.step
import clarity_epp.placement.tecan


app = typer.Typer()
app.add_typer(artifact.app, name="artifact")
app.add_typer(barcode.app, name="barcode")
app.add_typer(pipetting.app, name="pipetting")
app.add_typer(plate.app, name="plate")
app.add_typer(pool.app, name="pool")
app.add_typer(step.app, name="step")
app.add_typer(tecan.app, name="tecan")


if __name__ == "__main__":
    app()
