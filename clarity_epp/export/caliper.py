"""Caliper export functions."""

from genologics.entities import Process

import utils


def samplesheet_normalise(lims, process_id, output_file):
    """Create Caliper samplesheet for normalising 96 well plate."""
    output_file.write('Monsternummer\tPlate_Id_input\tWell\tPlate_Id_output\tPipetteervolume DNA (ul)\tPipetteervolume H2O (ul)\n')
    process = Process(lims, id=process_id)
    parent_processes = []
    parent_process_barcode_manual = 'None'
    parent_process_barcode_hamilton = 'None'
    for p in process.parent_processes():
        if 'Dx manueel gezuiverd placement' in p.type.name:
            for pp in p.parent_processes():
                parent_processes.append(pp)
            parent_process_barcode_manual = p.output_containers()[0].name
        if 'Dx Hamilton zuiveren' in p.type.name:
            parent_processes.append(p)
            parent_process_barcode_hamilton = p.output_containers()[0].name
        if 'Dx Zuiveren gDNA manueel' in p.type.name:
            parent_processes.append(p)
    if parent_process_barcode_hamilton != 'None':
        parent_process_barcode = parent_process_barcode_hamilton
    else:
        parent_process_barcode = parent_process_barcode_manual
    parent_processes = list(set(parent_processes))
    process_types = []
    types = []
    process_types = lims.get_process_types()
    for pt in process_types:
        if 'Dx Qubit QC' in pt.name:
            types.append(pt.name)
        elif 'Dx Tecan Spark 10M QC' in pt.name:
            types.append(pt.name)
    input_artifact_ids = []
    for p in parent_processes:
        for analyte in p.all_outputs():
            input_artifact_ids.append(analyte.id)
    input_artifact_ids = list(set(input_artifact_ids))
    qc_processes = lims.get_processes(
        type=[types],
        inputartifactlimsid=input_artifact_ids
    )
    qc_processes = list(set(qc_processes))
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

    for p in qc_processes:
        if 'Dx Qubit QC' in p.type.name:
            for a in p.all_outputs():
                if 'Tecan' not in a.name and 'check' not in a.name:
                    if 'Dx Conc. goedgekeurde meting (ng/ul)' in a.udf:
                        machine = 'Qubit'
                        sample = a.samples[0].name
                        measurement = a.udf['Dx Conc. goedgekeurde meting (ng/ul)']
                        qcflag = a.qc_flag
                        if qcflag == 'PASSED':
                            if sample in samples_measurements_qubit:
                                samples_measurements_qubit[sample].append(measurement)
                            else:
                                samples_measurements_qubit[sample] = [measurement]
                    else:
                        sample = a.samples[0].name
                        if sample not in sample_concentration:
                            sample_concentration[sample] = 'geen'
        elif 'Dx Tecan Spark 10M QC' in p.type.name:
            for a in p.all_outputs():
                if 'Tecan' not in a.name and 'check' not in a.name:
                    if 'Dx Conc. goedgekeurde meting (ng/ul)' in a.udf:
                        machine = 'Tecan'
                        sample = a.samples[0].name
                        measurement = a.udf['Dx Conc. goedgekeurde meting (ng/ul)']
                        qcflag = a.qc_flag
                        if qcflag == 'UNKNOWN' or 'PASSED':
                            if sample in samples_measurements_tecan:
                                samples_measurements_tecan[sample].append(measurement)
                            else:
                                samples_measurements_tecan[sample] = [measurement]
                    else:
                        sample = a.samples[0].name
                        if sample not in sample_concentration:
                            sample_concentration[sample] = 'geen'
    for p in qc_processes:
        for a in p.all_outputs():
            if 'Tecan' not in a.name and 'check' not in a.name:
                if 'Dx Tecan Spark 10M QC' in p.type.name:
                    if 'Dx Conc. goedgekeurde meting (ng/ul)' in a.udf:
                        machine = 'Tecan'
                    sample = a.samples[0].name
                elif 'Dx Qubit QC' in p.type.name:
                    if 'Dx Conc. goedgekeurde meting (ng/ul)' in a.udf:
                        machine = 'Qubit'
                    sample = a.samples[0].name
            if sample not in sample_concentration or machine == 'Qubit':
                if sample in samples_measurements_tecan or sample in samples_measurements_qubit:
                    if machine == 'Tecan':
                        sample_measurements = samples_measurements_tecan[sample]
                    elif machine == 'Qubit':
                        sample_measurements = samples_measurements_qubit[sample]
                    sample_measurements_average = sum(sample_measurements) / float(len(sample_measurements))
                    sample_concentration[sample] = sample_measurements_average

    for placement, artifact in process.output_containers()[0].placements.iteritems():
        placement = ''.join(placement.split(':'))
        filled_wells.append(placement)
        if order[placement] > last_filled_well:
            last_filled_well = order[placement]

    for x in range(0, last_filled_well):
        for well, number in order.iteritems():
            if number == x:
                placement = well
        monsternummer[placement] = 'Leeg'
        volume_DNA[placement] = 0
        volume_H2O[placement] = 0

    for placement, artifact in process.output_containers()[0].placements.iteritems():
        sample = artifact.samples[0].name
        placement = ''.join(placement.split(':'))
        monsternummer[placement] = sample
        conc_measured[placement] = sample_concentration[sample]
        if conc_measured[placement] != 'geen':
            if output_ng/conc_measured[placement] > 50:
                conc[placement] = output_ng/50
            else:
                conc[placement] = conc_measured[placement]
            volume_DNA[placement] = int(round(float(output_ng)/conc[placement]))
            volume_H2O[placement] = output_ul-int(round(float(output_ng)/conc[placement]))

    for well in utils.sort_96_well_plate(monsternummer.keys()):
        output_file.write('{monsternummer}\t{plate_id_input}\t{position}\t{plate_id_output}\t{volume_DNA}\t{volume_H2O}\n'.format(
            monsternummer=monsternummer[well],
            plate_id_input=parent_process_barcode,
            position=well,
            plate_id_output=output_plate_barcode,
            volume_DNA=volume_DNA[well],
            volume_H2O=volume_H2O[well]
        ))
