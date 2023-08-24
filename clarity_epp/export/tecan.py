"""Tecan export functions."""

from genologics.entities import Process

from .. import get_mix_sample_barcode
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
        # Samplesheet Tecan Fluent 480 'Dx Uitvullen en zuiveren' (mix) samples
        output_file.write(
            'SourceTubeID;VolSample;VolWater;PositionIndex;MengID\n'
        )

        # Find all QC process types
        qc_process_types = clarity_epp.export.utils.get_process_types(lims, ['Dx Qubit QC', 'Dx Tecan Spark 10M QC'])

        samples = {}
        # Find concentration in last QC process
        for input_artifact in process.all_inputs():
            for input_sample in input_artifact.samples:
                qc_processes = lims.get_processes(type=qc_process_types, inputartifactlimsid=input_artifact.id)
                if qc_processes:
                    qc_process = sorted(qc_processes, key=lambda process: int(process.id.split('-')[-1]))[-1]
                    for qc_artifact in qc_process.outputs_per_input(input_artifact.id):
                        if input_sample.name in qc_artifact.name:
                            for qc_sample in qc_artifact.samples:
                                if qc_sample.name == input_sample.name:
                                    concentration = float(qc_artifact.udf['Dx Concentratie fluorescentie (ng/ul)'])

                else:
                    parent_process = input_artifact.parent_process
                    for parent_artifact in parent_process.all_inputs():
                        if parent_artifact.name == input_sample.name:
                            qc_processes = lims.get_processes(type=qc_process_types, inputartifactlimsid=parent_artifact.id)
                            if qc_processes:
                                qc_process = sorted(qc_processes, key=lambda process: int(process.id.split('-')[-1]))[-1]
                                for qc_artifact in qc_process.outputs_per_input(parent_artifact.id):
                                    if input_sample.name in qc_artifact.name:
                                        for qc_sample in qc_artifact.samples:
                                            if qc_sample.name == input_sample.name:
                                                concentration = float(qc_artifact.udf['Dx Concentratie fluorescentie (ng/ul)'])
                            else:
                                # No QC process found, use Helix concentration
                                concentration = input_sample.udf['Dx Concentratie (ng/ul)']

                samples[input_sample.udf['Dx Monsternummer']] = {'conc': concentration}

        for well in clarity_epp.export.utils.sort_96_well_plate(well_plate.keys()):
            artifact = well_plate[well]
            sample_mix = False
            if len(artifact.samples) > 1:
                sample_mix = True

            if sample_mix:
                dividend = 880
                max_volume = 30
            else:
                dividend = 1760
                max_volume = 60

            for sample in artifact.samples:
                monster = sample.udf['Dx Monsternummer']
                samples[monster]['message'] = ''
                if sample_mix:
                    samples[monster]['mix_names'] = artifact.name
                else:
                    samples[monster]['mix_names'] = monster

                # Calculation of pipetting volumes
                calc_sample = dividend / samples[monster]['conc']
                if calc_sample < 4:
                    volume_sample = 4
                elif calc_sample > max_volume:
                    volume_sample = max_volume
                    samples[monster]['message'] = (
                        'Conc. too low - volume= {calc_sample} ul'.format(calc_sample=calc_sample)
                    )
                else:
                    volume_sample = calc_sample
                samples[monster]['sample_volume'] = volume_sample
                volume_water = max_volume - volume_sample
                samples[monster]['water_volume'] = volume_water

            for sample in artifact.samples:
                monster = sample.udf['Dx Monsternummer']
                output_file.write('{sample};{volume_sample:.2f};{volume_water:.2f};{index};{name};{empty};{message}\n'.format(
                    sample=sample.udf['Dx Fractienummer'],
                    volume_sample=samples[monster]['sample_volume'],
                    volume_water=samples[monster]['water_volume'],
                    index=clarity_epp.export.utils.get_well_index(well, one_based=True),
                    name=samples[monster]['mix_names'],
                    empty='',
                    message=samples[monster]['message']
                ))

    elif type == 'normalise':
        output_file.write('SourceTubeID;PositionID;PositionIndex\n')
        for well in clarity_epp.export.utils.sort_96_well_plate(well_plate.keys()):
            artifact = well_plate[well]
            if len(artifact.samples) > 1:
                source_tube = get_mix_sample_barcode(artifact)
            else:
                source_tube = sample.udf['Dx Fractienummer']
            output_file.write('{sample};{well};{index}\n'.format(
                sample=source_tube,
                well=well,
                index=clarity_epp.export.utils.get_well_index(well, one_based=True)
            ))