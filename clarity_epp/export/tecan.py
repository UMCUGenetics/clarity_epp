"""Tecan export functions."""

from genologics.entities import Process

import clarity_epp.export.utils


def samplesheet_qc(lims, process_id, type, output_file):
    """Create Tecan samplesheet."""
    process = Process(lims, id=process_id)
    well_plate = {}

    for placement, artifact in process.output_containers()[0].placements.items():
        placement = ''.join(placement.split(':'))
        if len(artifact.samples) == 1:  # Remove 'meet_id' from artifact name if artifact is not a pool
            well_plate[placement] = artifact.name.split('_')[0]
        else:
            well_plate[placement] = artifact.name

    if type == 'qc':
        output_file.write('Position\tSample\n')
        for well in clarity_epp.export.utils.sort_96_well_plate(well_plate.keys()):
            output_file.write('{well}\t{sample}\n'.format(
                well=well,
                sample=well_plate[well]
            ))

    elif type == 'purify_normalise':
        output_file.write('Sample\tPosition\n')
        for well in clarity_epp.export.utils.sort_96_well_plate(well_plate.keys()):
            output_file.write('{sample}\t{well}\n'.format(
                sample=well_plate[well],
                well=well
            ))