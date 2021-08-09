"""Tecan export functions."""

from genologics.entities import Process

import clarity_epp.export.utils


def samplesheet(lims, process_id, output_file):
    """Create Tecan samplesheet."""
    output_file.write('Position\tSample\n')
    process = Process(lims, id=process_id)
    well_plate = {}

    for placement, artifact in process.output_containers()[0].placements.items():
        placement = ''.join(placement.split(':'))
        if len(artifact.samples) == 1:  # Remove 'meet_id' from artifact name if artifact is not a pool
            well_plate[placement] = artifact.name.split('_')[0]
        else:
            well_plate[placement] = artifact.name

    for well in clarity_epp.export.utils.sort_96_well_plate(well_plate.keys()):
        output_file.write('{well}\t{sample}\n'.format(
            well=well,
            sample=well_plate[well]
        ))
