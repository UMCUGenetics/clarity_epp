"""Tecan export functions."""

from genologics.entities import Process

import clarity_epp.export.utils

from .. import get_mix_sample_barcode


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
                                    meter = 'Fluorescentiemeter'

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
                                                meter = 'Fluorescentiemeter'
                            else:
                                # No QC process found, use Helix concentration
                                concentration = input_sample.udf['Dx Concentratie (ng/ul)']
                                meter = input_sample.udf['Concentratie meting type']

                samples[input_sample.udf['Dx Monsternummer']] = {'conc': concentration, 'meter': meter}

        for well in clarity_epp.export.utils.sort_96_well_plate(well_plate.keys()):
            artifact = well_plate[well]
            input_ng = artifact.udf.get('Input (ng) zuivering')
            sample_mix = False
            if len(artifact.samples) > 1:
                sample_mix = True

            artifact_meters = []
            for sample in artifact.samples:
                monster = sample.udf['Dx Monsternummer']
                artifact_meters.append(samples[monster]['meter'])

            for sample in artifact.samples:
                monster = sample.udf['Dx Monsternummer']
                samples[monster]['message'] = ''

                if sample_mix:
                    samples[monster]['mix_names'] = artifact.name
                    # If other sample of smple_mix has a different meter change meter for this sample
                    if (len(set(artifact_meters)) > 1
                        and 'Spectrofotometer' in artifact_meters
                        and samples[monster]['meter'] != 'Spectrofotometer'):
                        samples[monster]['meter'] = 'Spectrofotometer'
                else:
                    samples[monster]['mix_names'] = monster

                if not input_ng:
                    samples[monster]['message'] = f'CF "Input (ng) zuivering" is leeg voor {artifact.name}'
                    samples[monster]['sample_volume'] = 'NB'
                    samples[monster]['water_volume'] = 'NB'
                else:
                    sample_concentration = samples[monster]['conc']
                    sample_concentration_meter = samples[monster]['meter']

                    if sample_concentration_meter == 'Fluorescentiemeter':
                        if sample_mix:  # Mengfractie met Fluorescentiemeter
                            dividend = input_ng / 2
                            max_volume = 30
                        else:  # Single sample met Fluorescentiemeter
                            dividend = input_ng
                            max_volume = 60
                    elif sample_concentration_meter == 'Spectrofotometer':
                        if sample_mix:  # Mengfractie met Spectrofotometer
                            dividend = input_ng
                            max_volume = 30
                        else:  # Single sample met Spectrofotometer
                            dividend = input_ng * 2
                            max_volume = 60

                    # Calculation of pipetting volumes
                    calc_sample = dividend / sample_concentration
                    if calc_sample < 4:
                        volume_sample = 4
                    elif calc_sample > max_volume:
                        volume_sample = max_volume
                        samples[monster]['message'] = (f'Concentratie te laag - volume= {calc_sample} ul')
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
        outputs = []
        for output in process.all_outputs():
            if output.name not in ['Dx labels nunc', 'Dx pipetteerschema manueel normaliseren', 'Dx Fluent480 samplesheet manueel normaliseren']:
                outputs.append(output.name)
        for well in clarity_epp.export.utils.sort_96_well_plate(well_plate.keys()):
            artifact = well_plate[well]
            if artifact.name in outputs:
                if len(artifact.samples) > 1:
                    source_tube = get_mix_sample_barcode(artifact)
                else:
                    sample = artifact.samples[0]
                    source_tube = sample.udf['Dx Fractienummer']
                output_file.write('{sample};{well};{index}\n'.format(
                    sample=source_tube,
                    well=well,
                    index=clarity_epp.export.utils.get_well_index(well, one_based=True)
                ))
