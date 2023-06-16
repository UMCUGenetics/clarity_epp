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
        output_file.write('SourceTubeID;PositionID;PositionIndex\n')
        for well in clarity_epp.export.utils.sort_96_well_plate(well_plate.keys()):
            artifact = well_plate[well]
            sample = artifact.samples[0]  # assume one sample per tube
            output_file.write('{sample};{well};{index}\n'.format(
                sample=sample.udf['Dx Fractienummer'],
                well=well,
                index=clarity_epp.export.utils.get_well_index(well, one_based=True)
            ))

    elif type == 'filling_out_purify':
        output_file.write(
            'SourceTubeID;VolSample;VolWater;PositionIndex;MengID\n'
        )
        for well in clarity_epp.export.utils.sort_96_well_plate(well_plate.keys()):
            artifact = well_plate[well]
            sample_mix = False
            if len(artifact.samples) > 1:
                sample_mix = True
            sample_volumes = {}
            water_volumes = {}
            mix_names = {}
            messages = {}
            for sample in artifact.samples:
                messages[sample] = ""
                conc = sample.udf['Dx Concentratie (ng/ul)']
                if sample_mix:
                    dividend = 880
                    max_volume = 30
                    mix_names[sample] = artifact.name
                else:
                    dividend = 1760
                    max_volume = 60
                    mix_names[sample] = sample.udf['Dx Monsternummer']
                calc_sample = dividend / conc
                if calc_sample < 4:
                    volume_sample = 4
                elif calc_sample > max_volume:
                    volume_sample = max_volume
                    messages[sample] = ("Conc. too low - volume= {calc_sample} ul".format(calc_sample=calc_sample))
                else:
                    volume_sample = calc_sample
                sample_volumes[sample] = volume_sample
                water_volumes[sample] = max_volume - volume_sample
            for sample in artifact.samples:
                output_file.write('{sample};{volume_sample:.2f};{volume_water:.2f};{index};{name};{empty};{message}\n'.format(
                    sample=sample.udf['Dx Fractienummer'],
                    volume_sample=sample_volumes[sample],
                    volume_water=water_volumes[sample],
                    index=clarity_epp.export.utils.get_well_index(well, one_based=True),
                    name=mix_names[sample],
                    empty="",
                    message=messages[sample]
                ))