"""Hamilton export functions."""

from genologics.entities import Process

import clarity_epp.export.utils


def samplesheet_filling_out(lims, process_id, output_file):
    """Create Hamilton samplesheet for filling out 96 well plate."""
    output_file.write('SourceTubeID\tPositionID\n')
    process = Process(lims, id=process_id)
    well_plate = {}

    for placement, artifact in process.output_containers()[0].placements.items():
        placement = ''.join(placement.split(':'))
        well_plate[placement] = artifact.samples[0].udf['Dx Fractienummer']

    for well in clarity_epp.export.utils.sort_96_well_plate(well_plate.keys()):
        output_file.write('{source_tube}\t{well}\n'.format(
            source_tube=well_plate[well],
            well=well
        ))


def samplesheet_purify(lims, process_id, output_file):
    """Create Hamilton samplesheet for purifying 96 well plate."""
    output_file.write('SampleID\tSample Rack barcode\tSample rack positionID\tSample Start volume\n')
    process = Process(lims, id=process_id)
    parent_process_barcode = process.parent_processes()[0].output_containers()[0].name
    well_plate = {}

    for placement, artifact in process.output_containers()[0].placements.items():
        placement = ''.join(placement.split(':'))
        well_plate[placement] = artifact.samples[0].udf['Dx Fractienummer']

    for well in clarity_epp.export.utils.sort_96_well_plate(well_plate.keys()):
        output_file.write('{sample}\t{sample_rack_barcode}\t{sample_rack_position}\t{sample_start_volume}\n'.format(
            sample=well_plate[well],
            sample_rack_barcode=parent_process_barcode,
            sample_rack_position=well,
            sample_start_volume='50'
        ))
