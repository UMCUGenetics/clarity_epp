"""Export functions."""

import typer

import clarity_epp.export.bioanalyzer
import clarity_epp.export.caliper
import clarity_epp.export.email
import clarity_epp.export.hamilton
import clarity_epp.export.illumina
import clarity_epp.export.labels
import clarity_epp.export.magnis
import clarity_epp.export.manual_pipetting
import clarity_epp.export.merge
import clarity_epp.export.myra
import clarity_epp.export.ped
import clarity_epp.export.sample
import clarity_epp.export.tapestation
import clarity_epp.export.tecan
import clarity_epp.export.workflow


app = typer.Typer()
app.add_typer(bioanalyzer.app, name="bioanalyzer")
app.add_typer(caliper.app, name="caliper")
app.add_typer(email.app, name="email")
app.add_typer(hamilton.app, name="hamilton")
app.add_typer(illumina.app, name="illumina")
app.add_typer(labels.app, name="labels")
app.add_typer(magnis.app, name="magnis")
app.add_typer(manual_pipetting.app, name="manual_pipetting")
app.add_typer(merge.app, name="merge")
app.add_typer(myra.app, name="myra")
app.add_typer(ped.app, name="ped")
app.add_typer(sample.app, name="sample")
app.add_typer(tapestation.app, name="tapestation")
app.add_typer(tecan.app, name="tecan")
app.add_typer(workflow.app, name="workflow")


if __name__ == "__main__":
    app()
