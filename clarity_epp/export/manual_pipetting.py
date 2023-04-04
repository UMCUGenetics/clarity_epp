"""Manual pipetting export functions."""
import re

from genologics.entities import Process

import clarity_epp.export.utils


def samplesheet_purify(lims, process_id, output_file):
    """Create manual pipetting samplesheet for purifying samples."""
    output_file.write('Fractienummer\tConcentration(ng/ul)\taantal ng te isoleren\tul gDNA\tul Water\n')
    process = Process(lims, id=process_id)
    # Find all QC process types
    qc_process_types = clarity_epp.export.utils.get_process_types(lims, ['Dx Qubit QC', 'Dx Tecan Spark 10M QC'])

    for container in process.output_containers():
        artifact = container.placements['1:1']  # asume tubes
        input_artifact = artifact.input_artifact_list()[0]  # asume one input artifact
        sample = artifact.samples[0]  # asume one sample per tube

        # Find last qc process for artifact
        qc_process = lims.get_processes(type=qc_process_types, inputartifactlimsid=input_artifact.id)
        if qc_process:
            qc_process = sorted(
                lims.get_processes(type=qc_process_types, inputartifactlimsid=input_artifact.id),
                key=lambda process: int(process.id.split('-')[-1])
            )[-1]
            for qc_artifact in qc_process.outputs_per_input(input_artifact.id):
                if qc_artifact.name.split(' ')[0] == artifact.name:
                    concentration = float(qc_artifact.udf['Dx Concentratie fluorescentie (ng/ul)'])

        else:  # Fallback on previous process if qc process not found.
            if 'Dx Concentratie fluorescentie (ng/ul)' in input_artifact.udf:
                concentration = float(input_artifact.udf['Dx Concentratie fluorescentie (ng/ul)'])
            elif 'Dx Concentratie OD (ng/ul)' in input_artifact.udf:
                concentration = float(input_artifact.udf['Dx Concentratie OD (ng/ul)'])
            elif 'Dx Concentratie (ng/ul)' in sample.udf:
                concentration = float(sample.udf['Dx Concentratie (ng/ul)'])

        if 'Dx Fractienummer' in sample.udf:
            fractienummer = sample.udf['Dx Fractienummer']
        else:  # giab
            fractienummer = sample.name

        input_gdna_ng = float(artifact.udf['Dx input hoeveelheid (ng)'])
        ul_gdna = input_gdna_ng/concentration
        ul_water = 200 - ul_gdna

        output_file.write('{fractienummer}\t{concentration}\t{input_gdna_ng}\t{ul_gdna:.1f}\t{ul_water:.1f}\n'.format(
            fractienummer=fractienummer,
            concentration=concentration,
            input_gdna_ng=input_gdna_ng,
            ul_gdna=ul_gdna,
            ul_water=ul_water
        ))


def samplesheet_dilute_library_pool(lims, process_id, output_file):
    """Create manual pipetting samplesheet for sequencing pools."""
    output_file.write('Sample\tContainer\tWell\tul Sample\tul EB\n')
    process = Process(lims, id=process_id)

    output = []  # save pool data to list, to be able to sort on pool number.
    nM_pool = process.udf['Dx Pool verdunning (nM)']
    output_ul = process.udf['Eindvolume (ul)']

    for input in process.all_inputs():
        search_number = re.search(r'Pool #(\d+)_', input.name)
        if search_number:
            input_number = int(search_number.group(1))
        else:
            input_number = 0
        qc_artifact = input.input_artifact_list()[0]

        size = float(qc_artifact.udf['Dx Fragmentlengte (bp)'])
        concentration = float(qc_artifact.udf['Dx Concentratie fluorescentie (ng/ul)'])

        nM_dna = (concentration * 1000 * (1/660.0) * (1/size)) * 1000
        ul_sample = (nM_pool/nM_dna) * output_ul
        ul_EB = output_ul - ul_sample

        line = '{pool_name}\t{container}\t{well}\t{ul_sample:.2f}\t{ul_EB:.2f}\n'.format(
            pool_name=input.name,
            container=input.location[0].name,
            well=input.location[1],
            ul_sample=ul_sample,
            ul_EB=ul_EB
        )
        output.append((input_number, line))

    for number, line in sorted(output):
        output_file.write(line)


def library_dilution_calculator(concentration, size, trio, pedigree, ng):
    """Calculate ul per sample needed for multiplexing."""
    if trio == 'CCC':
        ng_sample = 250
    elif trio == 'CPP' or trio == 'CCP':
        if pedigree == 'Kind':
            ng_sample = 266.1
        elif pedigree == 'Ouder':
            ng_sample = 241.9
    elif trio == 'not_3':
        ng_sample = 0
    elif trio == 'adapted':
        ng_sample = ng
    nM_DNA = (float(concentration)*(10.0**6.0))/(660*float(size))
    ul_sample = (float(ng_sample)*(10.0**6.0))/(660*float(size)*nM_DNA)
    return ul_sample


def library_dilution_calculator_fixed_volume(concentration, size, ul):
    """Calculate ng per sample (based on given ul_sample) needed for multiplexing."""
    nM_DNA = (float(concentration)*(10.0**6.0))/(660*float(size))
    ng_sample = (660*float(size)*nM_DNA*ul)/(10.0**6.0)
    return ng_sample


def library_dilution_calculator_fixed_ng(concentration, size, pedigree, ng, ped_given_ul):
    """Calculate ng per sample (based on calculated ng from given ul_sample) needed for multiplexing."""
    if pedigree == ped_given_ul:
        ng_sample = ng
    elif ped_given_ul == 'Kind' and pedigree == 'Ouder':
        ng_sample = ng/1.1
    elif ped_given_ul == 'Ouder' and pedigree == 'Kind':
        ng_sample = ng*1.1
    return ng_sample


def samplesheet_multiplex_library_pool(lims, process_id, output_file):
    """Create manual pipetting samplesheet for multiplexing(pooling) samples."""
    process = Process(lims, id=process_id)
    inputs = list(set(process.all_inputs()))
    outputs = list(set(process.all_outputs()))

    sample_concentration = {}
    sample_size = {}
    trio_statuses = {}
    ul_sample = {}
    ng_sample = {}
    udf_output = []
    udf_ul_sample = {}
    udf_name_ul_sample = {}
    plate_id = {}
    well_id = {}
    pools_not_3 = []
    order = [
        'A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1',
        'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2',
        'A3', 'B3', 'C3', 'D3', 'E3', 'F3', 'G3', 'H3',
        'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4',
        'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5', 'H5',
        'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6',
        'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7',
        'A8', 'B8', 'C8', 'D8', 'E8', 'F8', 'G8', 'H8',
        'A9', 'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9',
        'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10', 'H10',
        'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11',
        'A12', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12', 'H12'
    ]
    order = dict(zip(order, range(len(order))))
    well_order = {}
    sample_well_pool = []

    # get input udfs 'Dx sample volume ul' and 'Dx Samplenaam' per output analyte
    for output in outputs:
        if output.type == 'Analyte':
            if 'Dx sample volume (ul)' in output.udf and 'Dx Samplenaam' in output.udf:
                udf_ul_sample[output.name] = output.udf['Dx sample volume (ul)']
                # if samplename is complete sequencename take only monsternummer
                if re.search(r'U\d{6}\D{2}', output.udf['Dx Samplenaam']):
                    udf_name_ul_sample[output.name] = output.udf['Dx Samplenaam'][9:]
                else:
                    udf_name_ul_sample[output.name] = output.udf['Dx Samplenaam']
                udf_output.append(output.name)

    # get concentration, size, containername and well per input artifact
    for input in inputs:
        sample = input.samples[0]
        samplename = sample.name

        if 'Dx Concentratie fluorescentie (ng/ul)' in input.udf:
            measurement = input.udf['Dx Concentratie fluorescentie (ng/ul)']
            qcflag = input.qc_flag
            if qcflag == 'UNKNOWN' or 'PASSED':
                sample_concentration[samplename] = measurement

        if 'Dx Fragmentlengte (bp)' in input.udf:
            measurement = input.udf['Dx Fragmentlengte (bp)']
            qcflag = input.qc_flag
            if qcflag == 'UNKNOWN' or 'PASSED':
                sample_size[samplename] = measurement

        plate_id[samplename] = input.container.name
        placement = input.location[1]
        placement = ''.join(placement.split(':'))
        well_id[samplename] = placement
        well_order[sample.name] = order[placement]

    # get familystatus per sample in output analyte and determine trio composition if number of samples in pool = 3
    for output in outputs:
        if output.type == 'Analyte':
            sample_given_ul = ''
            if len(output.samples) == 3:
                samplestatus = []

                for sample in output.samples:
                    # First check GIAB controls
                    if 'CFGIAB' in sample.name.upper():
                        sample.udf['Dx Familie status'] = 'Kind'
                    elif 'PFGIAB' in sample.name.upper() or 'PMGIAB' in sample.name.upper():
                        sample.udf['Dx Familie status'] = 'Ouder'

                    if 'Dx Onderzoeksreden' in sample.udf and sample.udf['Dx Onderzoeksreden'] == 'Research':
                        samplestatus.append('Kind')
                    else:
                        samplestatus.append(sample.udf['Dx Familie status'])

                if samplestatus == ['Kind']*3 or samplestatus == ['Ouder']*3:
                    trio_statuses[output.name] = 'CCC'
                elif sorted(samplestatus) == ['Kind', 'Ouder', 'Ouder']:
                    trio_statuses[output.name] = 'CPP'
                elif sorted(samplestatus) == ['Kind', 'Kind', 'Ouder']:
                    trio_statuses[output.name] = 'CCP'

                # if udfs 'Dx sample volume ul' and 'Dx Samplenaam' are not empty change trio status and do pre-calculation
                if output.name in udf_output:
                    trio_statuses[output.name] = 'adapted'

                    for sample in output.samples:
                        if sample.name == udf_name_ul_sample[output.name]:
                            sample_given_ul = sample
                            ng_sample[sample.name] = library_dilution_calculator_fixed_volume(
                                sample_concentration[sample.name],
                                sample_size[sample.name],
                                udf_ul_sample[output.name]
                            )

                    for sample in output.samples:
                        if sample.name != udf_name_ul_sample[output.name]:
                            ng_sample[sample.name] = library_dilution_calculator_fixed_ng(
                                sample_concentration[sample.name],
                                sample_size[sample.name],
                                sample.udf['Dx Familie status'],
                                ng_sample[udf_name_ul_sample[output.name]],
                                sample_given_ul.udf['Dx Familie status']
                            )

                    output.udf['Dx input pool (ng)'] = round(
                        ng_sample[output.samples[0].name] +
                        ng_sample[output.samples[1].name] +
                        ng_sample[output.samples[2].name],
                        2
                    )
                    output.put()

                else:
                    output.udf['Dx input pool (ng)'] = 750
                    output.put()

            # if number of samples in pool is not 3 set trio status and prepare error warning output file
            else:
                trio_statuses[output.name] = 'not_3'
                pools_not_3.append(output.name)

            # calculation if udfs 'Dx sample volume ul' and 'Dx Samplenaam' are empty and not empty
            if not sample_given_ul:
                for sample in output.samples:
                    if 'Dx Onderzoeksreden' in sample.udf and sample.udf['Dx Onderzoeksreden'] == 'Research':
                        sample_pedigree = 'Kind'
                    else:
                        sample_pedigree = sample.udf['Dx Familie status']
                    ul_sample[sample.name] = library_dilution_calculator(
                        concentration=sample_concentration[sample.name],
                        size=sample_size[sample.name],
                        trio=trio_statuses[output.name],
                        pedigree=sample_pedigree,
                        ng=0
                    )
            else:
                for sample in output.samples:
                    if sample.udf['Dx Onderzoeksreden'] == 'Research':
                        sample_pedigree = 'Kind'
                    else:
                        sample_pedigree = sample.udf['Dx Familie status']
                    ul_sample[sample.name] = library_dilution_calculator(
                        concentration=sample_concentration[sample.name],
                        size=sample_size[sample.name],
                        trio=trio_statuses[output.name],
                        pedigree=sample_pedigree,
                        ng=ng_sample[sample.name]
                    )

            # sorting pools then wells for output file
            sort_pool_name = output.name
            if re.search(r'#\d_', sort_pool_name):
                sort_pool_name = re.sub('#', '#0', sort_pool_name)
            for sample in output.samples:
                sample_well_pool.append([sample, well_order[sample.name], sort_pool_name, output.name])

    sorted_samples = sorted(sample_well_pool, key=lambda sample: (sample[2], sample[1]))

    # write output file per output analyte sorted on pool number
    output_file.write('Sample\tul Sample\tPlaat_id\twell_id\tpool\n')
    if pools_not_3:
        output_file.write('De volgende pool(s) hebben een ander aantal samples dan 3: {pools}\n'.format(pools=pools_not_3))

    for sorted_sample in sorted_samples:
        sample = sorted_sample[0]

        output_file.write('{sample}\t{ul_sample:.2f}\t{plate_id}\t{well_id}\t{pool}\n'.format(
            sample=sample.name,
            ul_sample=ul_sample[sample.name],
            plate_id=plate_id[sample.name],
            well_id=well_id[sample.name],
            pool=sorted_sample[3]
        ))


def samplesheet_multiplex_sequence_pool(lims, process_id, output_file):
    """Create manual pipetting samplesheet for multiplex sequence pools."""

    process = Process(lims, id=process_id)
    input_pools = []
    total_sample_count = 0
    total_load_uL = 0
    final_volume = float(process.udf['Final volume'].split()[0])

    for input_pool in process.all_inputs():
        input_pool_conc = float(input_pool.udf['Dx Concentratie fluorescentie (ng/ul)'])
        input_pool_size = float(input_pool.udf['Dx Fragmentlengte (bp)'])
        input_pool_nM = (input_pool_conc * 1000 * (1.0/660.0) * (1/input_pool_size)) * 1000
        input_pool_pM = (input_pool_nM * 1000) / 5

        input_pool_sample_count = 0

        for sample in input_pool.samples:
            if 'Dx Exoomequivalent' in sample.udf:
                input_pool_sample_count += sample.udf['Dx Exoomequivalent']
            else:
                input_pool_sample_count += 1
        total_sample_count += input_pool_sample_count
        input_pools.append({
            'name': input_pool.name,
            'nM': input_pool_nM,
            'pM': input_pool_pM,
            'sample_count': input_pool_sample_count
        })

    # print header
    output_file.write('Naam\tuL\n')

    # Last calcuations and print sample
    for input_pool in input_pools:
        input_pool_load_pM = (float(process.udf['Dx Laadconcentratie (pM)'])/total_sample_count) * input_pool['sample_count']
        input_pool_load_uL = final_volume / (input_pool['pM']/input_pool_load_pM)
        total_load_uL += input_pool_load_uL
        output_file.write('{0}\t{1:.2f}\n'.format(input_pool['name'], input_pool_load_uL))

    tris_HCL_uL = final_volume - total_load_uL
    output_file.write('{0}\t{1:.2f}\n'.format('Tris-HCL', tris_HCL_uL))


def samplesheet_normalization(lims, process_id, output_file):
    """Create manual pipetting samplesheet for normalizing (MIP) samples."""
    output_file.write(
        'Sample\tConcentration (ng/ul)\tVolume sample (ul)\tVolume water (ul)\tOutput (ng)\tIndampen\tContainer\tWell\n'
    )
    process = Process(lims, id=process_id)
    output = {}

    # Find all QC process types
    qc_process_types = clarity_epp.export.utils.get_process_types(lims, ['Dx Qubit QC', 'Dx Tecan Spark 10M QC'])

    for input_artifact in process.all_inputs(resolve=True):
        artifact = process.outputs_per_input(input_artifact.id, Analyte=True)[0]  # assume one artifact per input
        sample = input_artifact.samples[0]  # asume one sample per input artifact

        # Find last qc process for artifact
        qc_process = lims.get_processes(type=qc_process_types, inputartifactlimsid=input_artifact.id)
        if qc_process:
            qc_process = sorted(
                lims.get_processes(type=qc_process_types, inputartifactlimsid=input_artifact.id),
                key=lambda process: int(process.id.split('-')[-1])
            )[-1]
            qc_artifacts = qc_process.outputs_per_input(input_artifact.id)
        else:  # Fallback on previous process if qc process not found.
            qc_process = input_artifact.parent_process
            qc_artifacts = qc_process.all_outputs()

        # Find concentration measurement
        for qc_artifact in qc_artifacts:
            if qc_artifact.name.split(' ')[0] == artifact.name:
                concentration = float(qc_artifact.udf['Dx Concentratie fluorescentie (ng/ul)'])

        final_volume = float(artifact.udf['Dx Eindvolume (ul)'])
        input_ng = float(artifact.udf['Dx Input (ng)'])
        if 'Dx pipetteervolume (ul)' in artifact.udf:
            input_ng = concentration * float(artifact.udf['Dx pipetteervolume (ul)'])

        sample_volume = input_ng / concentration
        water_volume = final_volume - sample_volume
        evaporate = 'N'

        if sample_volume < 0.5:
            sample_volume = 0.5
            water_volume = final_volume - sample_volume
        elif sample_volume > final_volume:
            evaporate = 'J'
            water_volume = 0

        # Save output under container location (well)
        well = ''.join(artifact.location[1].split(':'))
        output_data = (
            '{sample}\t{concentration:.1f}\t{sample_volume:.1f}\t{water_volume:.1f}\t'
            '{output:.1f}\t{evaporate}\t{container}\t{well}\n'
        ).format(
            sample=sample.name,
            concentration=concentration,
            sample_volume=sample_volume,
            water_volume=water_volume,
            output=input_ng,
            evaporate=evaporate,
            container=artifact.location[0].name,
            well=well
        )
        if well == '11':  # Tube
            output_file.write(output_data)
        else:  # plate
            output[well] = output_data

    for well in clarity_epp.export.utils.sort_96_well_plate(output.keys()):
        output_file.write(output[well])


def samplesheet_capture(lims, process_id, output_file):
    """Create manual pipetting samplesheet for capture protocol."""
    process = Process(lims, id=process_id)
    sample_count = len(process.analytes()[0])

    # All input paramters
    data = [
        ['Ampligase Buffer 10X', process.udf['Ampligase Buffer 10X']],
        ['MIP pool werkoplossing', process.udf['MIP pool werkoplossing']],
        ['*dNTP 0.25mM', process.udf['*dNTP 0.25mM']],
        ['Hemo Klentaq 10U/ul', process.udf['Hemo Klentaq 10U/ul']],
        ['Ampligase 100U/ul', process.udf['Ampligase 100U/ul']],
        ['Water', process.udf['Water']],
    ]

    # Caculate for sample count
    for i, item in enumerate(data):
        data[i].append(sample_count * item[1] * 1.1)

    # Calculate final volume
    data.append([
        'ul MM in elke well',
        sum([item[1] for item in data]),
        sum([item[2] for item in data]),
    ])

    # Write samplesheet
    output_file.write('Mastermix\t1\t{0}\n'.format(sample_count))
    for item in data:
        output_file.write('{0}\t{1:.2f}\t{2:.2f}\n'.format(item[0], item[1], item[2]))


def sammplesheet_exonuclease(lims, process_id, output_file):
    """Create manual pipetting samplesheet for Exonuclease protocol"""
    process = Process(lims, id=process_id)
    sample_count = len(process.analytes()[0])

    # All input paramters
    data = [
        ['EXO I', process.udf['EXO I']],
        ['EXO III', process.udf['EXO III']],
        ['Ampligase buffer 10X', process.udf['Ampligase buffer 10X']],
        ['H2O', process.udf['H2O']],
    ]

    # Caculate for sample count
    for i, item in enumerate(data):
        data[i].append(sample_count * item[1] * 1.30)

    # Calculate total
    data.append([
        'TOTAL (incl. 30% overmaat)',
        sum([item[1] for item in data]),
        sum([item[2] for item in data]),
    ])

    # Write samplesheet
    output_file.write('\tMaster Mix (ul)\t{0}\n'.format(sample_count))
    for item in data:
        output_file.write('{0}\t{1:.2f}\t{2:.2f}\n'.format(item[0], item[1], item[2]))


def sammplesheet_pcr_exonuclease(lims, process_id, output_file):
    """Create manual pipetting samplesheet for PCR after Exonuclease protocol"""
    process = Process(lims, id=process_id)
    sample_count = len(process.analytes()[0])

    # All input paramters
    data = [
        ['2X iProof', process.udf['2X iProof']],
        ['Illumina forward primer(100uM) MIP_OLD_BB_FOR', process.udf['Illumina forward primer(100uM) MIP_OLD_BB_FOR']],
        ['H2O', process.udf['H2O']],
    ]

    # Caculate for sample count
    for i, item in enumerate(data):
        data[i].append(sample_count * item[1] * 1.1)

    # Calculate total
    data.append([
        'TOTAL (incl. 10% overmaat)',
        sum([item[1] for item in data]) * 1.1,
        sum([item[2] for item in data]),
    ])

    # Write samplesheet
    output_file.write('\tMaster Mix (ul)\t{0}\n'.format(sample_count))
    for item in data:
        output_file.write('{0}\t{1:.2f}\t{2:.2f}\n'.format(item[0], item[1], item[2]))


def samplesheet_mip_multiplex_pool(lims, process_id, output_file):
    """Create manual pipetting samplesheet for smMIP multiplexing"""
    process = Process(lims, id=process_id)
    input_artifacts = []

    # Find all Dx Tapestation 2200/4200 QC process types
    qc_process_types = clarity_epp.export.utils.get_process_types(lims, ['Dx Tapestation 2200 QC', 'Dx Tapestation 4200 QC'])

    # Write header
    output_file.write('{sample}\t{volume}\t{plate_id}\t{well_id}\t{concentration}\t{manual}\n'.format(
            sample='Sample',
            volume='Volume',
            plate_id='Plaat_id',
            well_id='Well_id',
            concentration='Concentratie',
            manual='Handmatig',
        ))

    for input_artifact in process.all_inputs(resolve=True):
        concentration = None
        # Find last qc process for artifact
        qc_processes = lims.get_processes(type=qc_process_types, inputartifactlimsid=input_artifact.id)

        if qc_processes:
            qc_process = sorted(qc_processes, key=lambda process: int(process.id.split('-')[-1]))[-1]
            # Find concentration measurement
            for qc_artifact in qc_process.outputs_per_input(input_artifact.id):
                if qc_artifact.name == input_artifact.name:
                    concentration = float(qc_artifact.udf['Dx Concentratie fluorescentie (ng/ul)'])

        input_artifacts.append({
            'name': input_artifact.name,
            'concentration': concentration,
            'plate_id': input_artifact.location[0].id,
            'well_id': ''.join(input_artifact.location[1].split(':')),
            'manual': input_artifact.samples[0].udf['Dx Handmatig']
        })

    # Calculate avg concentration for all non manual samples with a measured concentration
    concentrations = [
        input_artifact['concentration'] for input_artifact in input_artifacts
        if input_artifact['concentration'] and not input_artifact['manual']
    ]
    avg_concentration = sum(concentrations) / len(concentrations)

    # Set volume and store input_artifact per plate to be able print samplesheet sorted on plate and well
    input_containers = {}
    for input_artifact in input_artifacts:
        # Set avg concentration as concentration for artifacts without a measured concentration
        if not input_artifact['concentration']:
            input_artifact['concentration'] = avg_concentration

        # Set volumes
        if input_artifact['concentration'] < avg_concentration * 0.5:
            input_artifact['volume'] = 20
        elif input_artifact['concentration'] > avg_concentration * 1.5:
            input_artifact['volume'] = 1
        else:
            input_artifact['volume'] = 2

        if input_artifact['plate_id'] not in input_containers:
            input_containers[input_artifact['plate_id']] = {}

        input_containers[input_artifact['plate_id']][input_artifact['well_id']] = input_artifact

    for input_container in sorted(input_containers.keys()):
        input_artifacts = input_containers[input_container]
        for well in clarity_epp.export.utils.sort_96_well_plate(input_artifacts.keys()):
            input_artifact = input_artifacts[well]
            output_file.write('{sample}\t{volume}\t{plate_id}\t{well_id}\t{concentration:.3f}\t{manual}\n'.format(
                sample=input_artifact['name'],
                volume=input_artifact['volume'],
                plate_id=input_artifact['plate_id'],
                well_id=input_artifact['well_id'],
                concentration=input_artifact['concentration'],
                manual=input_artifact['manual'],
            ))


def samplesheet_mip_pool_dilution(lims, process_id, output_file):
    """Create manual pipetting samplesheet for smMIP pool dilution"""
    process = Process(lims, id=process_id)

    # Write header
    output_file.write((
        '{sample}\t{ul_sample_10}\t{ul_EB_10}\t{ul_sample_20}\t{ul_EB_20}\t{ul_sample_40}\t{ul_EB_40}\t\n'
    ).format(
        sample='Sample',
        ul_sample_10='ul Sample (10 ul)',
        ul_EB_10='ul EB buffer (10 ul)',
        ul_sample_20='ul Sample (20 ul)',
        ul_EB_20='ul EB buffer (20 ul)',
        ul_sample_40='ul Sample (40 ul)',
        ul_EB_40='ul EB buffer (40 ul)',
    ))

    for input_artifact in process.all_inputs(resolve=True):
        concentration = float(input_artifact.udf['Dx Concentratie fluorescentie (ng/ul)'])
        fragment_length = float(input_artifact.udf['Dx Fragmentlengte (bp)'])

        dna = (concentration * (10.0**3.0 / 1.0) * (1.0 / 649.0) * (1.0 / fragment_length)) * 1000.0
        ul_sample = 2 / dna * 10
        ul_EB = 10 - ul_sample

        output_file.write((
            '{sample}\t{ul_sample_10:.2f}\t{ul_EB_10:.2f}\t{ul_sample_20:.2f}\t{ul_EB_20:.2f}\t'
            '{ul_sample_40:.2f}\t{ul_EB_40:.2f}\t\n'
        ).format(
            sample=input_artifact.name,
            ul_sample_10=ul_sample,
            ul_EB_10=ul_EB,
            ul_sample_20=ul_sample * 2,
            ul_EB_20=ul_EB * 2,
            ul_sample_40=ul_sample * 4,
            ul_EB_40=ul_EB * 4,
        ))


def samplesheet_pool_samples(lims, process_id, output_file):
    """Create manual pipetting samplesheet for pooling samples."""
    process = Process(lims, id=process_id)

    # print header
    output_file.write('Sample\tContainer\tWell\tPool\tVolume (ul)\n')

    # Get all input artifact and store per container
    input_containers = {}
    for input_artifact in process.all_inputs(resolve=True):
        container = input_artifact.location[0].name
        well = ''.join(input_artifact.location[1].split(':'))

        if container not in input_containers:
            input_containers[container] = {}

        input_containers[container][well] = input_artifact

    # print pool scheme per input artifact
    # sort on container and well
    for input_container in sorted(input_containers.keys()):
        input_artifacts = input_containers[input_container]
        for well in clarity_epp.export.utils.sort_96_well_plate(input_artifacts.keys()):
            input_artifact = input_artifacts[well]
            input_sample = input_artifact.samples[0]  # Asume one sample

            if 'Dx Exoomequivalent' in input_sample.udf:
                volume = 5 * input_sample.udf['Dx Exoomequivalent']
            else:
                volume = 5

            output_file.write(
                '{sample}\t{container}\t{well}\t{pool}\t{volume}\n'.format(
                    sample=input_artifact.name,
                    container=input_artifact.location[0].name,
                    well=well,
                    pool=process.outputs_per_input(input_artifact.id, Analyte=True)[0].name,
                    volume=volume
                )
            )


def samplesheet_pool_magnis_pools(lims, process_id, output_file):
    """Create manual pipetting samplesheet for pooling magnis pools. Correct for pools with < 8 samples"""
    process = Process(lims, id=process_id)

    # print header
    output_file.write('Pool\tContainer\tSample count\tVolume (ul)\n')

    # Get input pools, sort by name and print volume
    for input_artifact in sorted(process.all_inputs(resolve=True), key=lambda artifact: artifact.id):
        sample_count = 0
        for sample in input_artifact.samples:
            if 'Dx Exoomequivalent' in sample.udf:
                sample_count += sample.udf['Dx Exoomequivalent']
            else:
                sample_count += 1

        output_file.write(
            '{pool}\t{container}\t{sample_count}\t{volume}\n'.format(
                pool=input_artifact.name,
                container=input_artifact.container.name,
                sample_count=sample_count,
                volume=sample_count * 1.25
            )
        )
