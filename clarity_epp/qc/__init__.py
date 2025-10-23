"""Automatic QC functions."""

import typer

import clarity_epp.qc.bioinformatics
import clarity_epp.qc.fragment_length
import clarity_epp.qc.illumina
import clarity_epp.qc.qubit
import clarity_epp.qc.sample


app = typer.Typer()
app.add_typer(bioinformatics.app, name="bioinformatics")
app.add_typer(fragment_length.app, name="fragment_length")
app.add_typer(illumina.app, name="illumina")
app.add_typer(qubit.app, name="qubit")
app.add_typer(sample.app, name="sample")


if __name__ == "__main__":
    app()
