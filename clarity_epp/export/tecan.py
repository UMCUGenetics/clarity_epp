"""Tecan export functions."""

from genologics.entities import Process

import clarity_epp.export.utils


def samplesheet(lims, process_id, type, output_file):
    """Create Tecan samplesheet."""
    process = Process(lims, id=process_id)
    well_plate = {}

    for placement, artifact in process.output_containers()[0].placements.items():
        placement = ''.join(placement.split(':'))
        well_plate[placement] = artifact

    if type == 'qc':
        output_file.write('Position\tSample\n')
        for well in clarity_epp.export.utils.sort_96_well_plate(well_plate.keys()):
            # Set correct artifact name
            artifact = well_plate[well]
            if len(artifact.samples) == 1:
                artifact_name = artifact.name.split('_')[0]
            else:
                artifact_name = artifact.name

            output_file.write('{well}\t{artifact}\n'.format(
                well=well,
                artifact=artifact_name
            ))

    elif type == 'purify_normalise':
        output_file.write('SourceTubeID\tPositionID\tPositionIndex\n')
        for well in clarity_epp.export.utils.sort_96_well_plate(well_plate.keys()):
            artifact = well_plate[well]
            sample = artifact.samples[0]  # assume one sample per tube
            output_file.write('{sample}\t{well}\t{index}\n'.format(
                sample=sample.udf['Dx Fractienummer'],
                well=well,
                index=clarity_epp.export.utils.get_well_index(well, one_based=True)
            ))
