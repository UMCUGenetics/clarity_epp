"""Tecan samplesheet epp functions."""

from genologics.entities import Process

import utils


def run_tecan(lims, process_id, output_file):
    """Create Tecan samplesheet."""
    output_file.write('Position\tSample\n')
    process = Process(lims, id=process_id)
    well_plate = {}

    for placement, artifact in process.output_containers()[0].placements.iteritems():
        placement = ''.join(placement.split(':'))

        if 'Dx Monsternummer' in artifact.samples[0].udf:
            well_plate[placement] = artifact.samples[0].udf['Dx Monsternummer']
        else:
            well_plate[placement] = artifact.samples[0].name  # Sample is assumed to be tecan control

    for well in utils.sort_96_well_plate(well_plate.keys()):
        output_file.write('{well}\t{sample}\n'.format(
            well=well,
            sample=well_plate[well]
        ))
