#!venv/bin/python
"""Clarity epp application."""

import sys
import argparse

import typer
import genologics.lims
from tenacity import Retrying, RetryError, stop_after_attempt, wait_fixed

from clarity_epp import export
from clarity_epp import upload
from clarity_epp import qc
from clarity_epp import placement

import config


# Setup lims connection and try connection twice
lims = genologics.lims.Lims(config.baseuri, config.username, config.password)
genologics.lims.TIMEOUT = config.api_timeout

try:
    for lims_connection_attempt in Retrying(stop=stop_after_attempt(2), wait=wait_fixed(1)):
        with lims_connection_attempt:
            lims.check_version()
except RetryError:
    raise Exception("Could not connect to Clarity LIMS.")


app = typer.Typer()
app.add_typer(export.app, name="export")
app.add_typer(upload.app, name="upload")
app.add_typer(qc.app, name="qc")
app.add_typer(placement.app, name="placement")


if __name__ == "__main__":
    app()
