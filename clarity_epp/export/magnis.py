"""Magnis export functions."""

from genologics.entities import Process

import clarity_epp.export.utils


def samplesheet(lims, process_id, output_file):
    """Create Magnis samplesheet."""
    process = Process(lims, id=process_id)
    well_strip = {}

    for placement, artifact in process.output_containers()[0].placements.items():
        placement = ''.join(placement.split(':'))
        well_strip[placement] = artifact.name

    for well in clarity_epp.export.utils.sort_96_well_plate(well_strip.keys()):
        output_file.write('{sample}\n'.format(sample=well_strip[well]))
