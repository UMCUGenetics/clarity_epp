"""Tapestation export functions."""

from genologics.entities import Process

import clarity_epp.export.utils as utils


def samplesheet(lims, process_id, output_file):
    """Create Tapestation samplesheet."""
    process = Process(lims, id=process_id)
    well_plate = {}

    for placement, artifact in process.output_containers()[0].placements.iteritems():
        placement = ''.join(placement.split(':'))
        well_plate[placement] = artifact.name.split('_')[0]

    for well in utils.sort_96_well_plate(well_plate.keys()):
        output_file.write('{sample}\n'.format(
            sample=well_plate[well]
        ))
