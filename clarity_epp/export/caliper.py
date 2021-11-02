"""Caliper export functions."""

from genologics.entities import Process

import clarity_epp.export.utils


def samplesheet_normalise(lims, process_id, output_file):
    """Create Caliper samplesheet for normalising 96 well plate."""
    output_file.write(
        'Monsternummer\tPlate_Id_input\tWell\tPlate_Id_output\tPipetteervolume DNA (ul)\tPipetteervolume H2O (ul)\n'
    )
    process = Process(lims, id=process_id)
    process_samples = [artifact.name for artifact in process.analytes()[0]]
    parent_processes = []
    parent_process_barcode_manual = 'None'
    parent_process_barcode_hamilton = 'None'

    for p in process.parent_processes():
        if p.type.name.startswith('Dx manueel gezuiverd placement'):
            for pp in p.parent_processes():
                parent_processes.append(pp)
            parent_process_barcode_manual = p.output_containers()[0].name
        elif p.type.name.startswith('Dx Hamilton'):
            parent_processes.append(p)
            parent_process_barcode_hamilton = p.output_containers()[0].name
        elif p.type.name.startswith('Dx Zuiveren gDNA manueel'):
            parent_processes.append(p)

    if parent_process_barcode_hamilton != 'None':
        parent_process_barcode = parent_process_barcode_hamilton
    else:
        parent_process_barcode = parent_process_barcode_manual

    # Get all Qubit and Tecan Spark QC types
    qc_process_types = clarity_epp.export.utils.get_process_types(lims, ['Dx Qubit QC, Dx Tecan Spark 10M QC'])

    # Get all unique input artifact ids
    parent_processes = list(set(parent_processes))
    input_artifact_ids = []
    for p in parent_processes:
        for analyte in p.all_outputs():
            input_artifact_ids.append(analyte.id)
    input_artifact_ids = list(set(input_artifact_ids))

    # Get unique QC processes for input artifacts
    qc_processes = list(set(lims.get_processes(type=qc_process_types, inputartifactlimsid=input_artifact_ids)))

    samples_measurements_qubit = {}
    sample_concentration = {}
    samples_measurements_tecan = {}
    filled_wells = []
    order = [
        'A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2',
        'A3', 'B3', 'C3', 'D3', 'E3', 'F3', 'G3', 'H3', 'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4',
        'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5', 'H5', 'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6',
        'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7', 'A8', 'B8', 'C8', 'D8', 'E8', 'F8', 'G8', 'H8',
        'A9', 'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9', 'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10', 'H10',
        'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11', 'A12', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12', 'H12'
    ]
    order = dict(zip(order, range(len(order))))
    last_filled_well = 0
    monsternummer = {}
    volume_DNA = {}
    volume_H2O = {}
    conc_measured = {}
    output_ng = process.udf['Output genormaliseerd gDNA']
    conc = {}
    output_ul = process.udf['Eindvolume (ul) genormaliseerd gDNA']
    output_plate_barcode = process.output_containers()[0].name

    for qc_process in qc_processes:
        if 'Dx Qubit QC' in qc_process.type.name:
            for artifact in qc_process.all_outputs():
                sample = artifact.samples[0].name
                if sample in process_samples and not any(keyword in artifact.name for keyword in ['Tecan', 'check', 'Label']):
                    if 'Dx Conc. goedgekeurde meting (ng/ul)' in artifact.udf:
                        measurement = artifact.udf['Dx Conc. goedgekeurde meting (ng/ul)']
                        if sample not in samples_measurements_qubit:
                            samples_measurements_qubit[sample] = []
                        samples_measurements_qubit[sample].append(measurement)
                    elif sample not in sample_concentration:
                        sample_concentration[sample] = 'geen'

        elif 'Dx Tecan Spark 10M QC' in qc_process.type.name:
            for artifact in qc_process.all_outputs():
                sample = artifact.samples[0].name
                if sample in process_samples and not any(keyword in artifact.name for keyword in ['Tecan', 'check', 'Label']):
                    if 'Dx Conc. goedgekeurde meting (ng/ul)' in artifact.udf:
                        measurement = artifact.udf['Dx Conc. goedgekeurde meting (ng/ul)']
                        if sample not in samples_measurements_tecan:
                            samples_measurements_tecan[sample] = []
                        samples_measurements_tecan[sample].append(measurement)
                    elif sample not in sample_concentration:
                        sample_concentration[sample] = 'geen'

    for qc_process in qc_processes:
        for artifact in qc_process.all_outputs():
            sample = artifact.samples[0].name
            if not any(keyword in artifact.name for keyword in ['Tecan', 'check', 'Label']):
                if 'Dx Tecan Spark 10M QC' in qc_process.type.name and 'Dx Conc. goedgekeurde meting (ng/ul)' in artifact.udf:
                    machine = 'Tecan'
                elif 'Dx Qubit QC' in qc_process.type.name and 'Dx Conc. goedgekeurde meting (ng/ul)' in artifact.udf:
                    machine = 'Qubit'

                if sample not in sample_concentration or machine == 'Qubit':
                    if sample in samples_measurements_tecan or sample in samples_measurements_qubit:
                        if machine == 'Tecan':
                            sample_measurements = samples_measurements_tecan[sample]
                        elif machine == 'Qubit':
                            sample_measurements = samples_measurements_qubit[sample]
                        sample_measurements_average = sum(sample_measurements) / float(len(sample_measurements))
                        sample_concentration[sample] = sample_measurements_average

    for placement, artifact in process.output_containers()[0].placements.items():
        placement = ''.join(placement.split(':'))
        filled_wells.append(placement)
        if order[placement] > last_filled_well:
            last_filled_well = order[placement]

    for x in range(0, last_filled_well):
        for well, number in order.items():
            if number == x:
                placement = well
        monsternummer[placement] = 'Leeg'
        volume_DNA[placement] = 0
        volume_H2O[placement] = 0

    for placement, artifact in process.output_containers()[0].placements.items():
        sample = artifact.samples[0].name
        if sample in process_samples:
            placement = ''.join(placement.split(':'))
            monsternummer[placement] = sample
            conc_measured[placement] = sample_concentration[sample]
            if conc_measured[placement] != 'geen':
                if output_ng/conc_measured[placement] > 100:
                    conc[placement] = output_ng/100
                else:
                    conc[placement] = conc_measured[placement]
                volume_DNA[placement] = int(round(float(output_ng)/conc[placement]))
                volume_H2O[placement] = output_ul-int(round(float(output_ng)/conc[placement]))

    for well in clarity_epp.export.utils.sort_96_well_plate(monsternummer.keys()):
        output_file.write(
            '{monsternummer}\t{plate_id_input}\t{position}\t{plate_id_output}\t{volume_DNA}\t{volume_H2O}\n'.format(
                monsternummer=monsternummer[well],
                plate_id_input=parent_process_barcode,
                position=well,
                plate_id_output=output_plate_barcode,
                volume_DNA=volume_DNA[well],
                volume_H2O=volume_H2O[well]
            )
        )


def samplesheet_dilute(lims, process_id, output_file):
    """Create Caliper samplesheet for diluting samples."""
    # output_file.write('Sample\tContainer\tWell\tul Sample\tul EB\n')
    output_file.write(
        'Monsternummer\tPlate_Id_input\tWell\tPlate_Id_output\tPipetteervolume DNA (ul)\tPipetteervolume H2O (ul)\n'
    )
    process = Process(lims, id=process_id)

    output = {}  # save output data to dict, to be able to sort on well.
    nM_pool = process.udf['Dx Pool verdunning (nM)']
    output_ul = process.udf['Eindvolume (ul)']

    for input_artifact in process.all_inputs():
        output_artifact = process.outputs_per_input(input_artifact.id, Analyte=True)[0]

        # Get QC stats
        size = float(input_artifact.udf['Dx Fragmentlengte (bp)'])
        concentration = float(input_artifact.udf['Dx Concentratie fluorescentie (ng/ul)'])

        # Calculate dilution
        nM_dna = (concentration * 1000 * (1/660.0) * (1/size)) * 1000
        ul_sample = (nM_pool/nM_dna) * output_ul
        ul_water = output_ul - ul_sample

        # Store output lines by well
        well = ''.join(input_artifact.location[1].split(':'))
        output[well] = '{name}\t{plate_id_input}\t{well}\t{plate_id_output}\t{volume_dna}\t{volume_water}\n'.format(
            name=input_artifact.name,
            plate_id_input=input_artifact.location[0].id,
            well=well,
            plate_id_output=output_artifact.location[0].id,
            volume_dna=ul_sample,
            volume_water=ul_water
        )

    # Write output, sort by well
    for well in clarity_epp.export.utils.sort_96_well_plate(output.keys()):
        output_file.write(output[well])
