"""Manual pipetting export functions."""
import re

from genologics.entities import Process


def samplesheet_purify(lims, process_id, output_file):
    """Create manual pipetting samplesheet for purifying samples."""
    output_file.write('Fractienummer\tConcentration(ng/ul)\taantal ng te isoleren\tul gDNA\tul Water\n')
    process = Process(lims, id=process_id)

    for container in process.output_containers():
        artifact = container.placements['1:1']  # asume tubes
        input_artifact = artifact.input_artifact_list()[0]  # asume one input artifact
        sample = artifact.samples[0]  # asume one sample per tube

        fractienummer = sample.udf['Dx Fractienummer']

        if 'Dx Concentratie fluorescentie (ng/ul)' in input_artifact.udf:
                concentration = float(input_artifact.udf['Dx Concentratie fluorescentie (ng/ul)'])
        elif 'Dx Concentratie OD (ng/ul)' in input_artifact.udf:
                concentration = float(input_artifact.udf['Dx Concentratie OD (ng/ul)'])
        elif 'Dx Concentratie (ng/ul)' in sample.udf:
                concentration = float(sample.udf['Dx Concentratie (ng/ul)'])

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


def samplesheet_sequencing_pool(lims, process_id, output_file):
    """Create manual pipetting samplesheet for sequencing pools."""
    output_file.write('Sample pool\tul Sample\tul EB\n')
    process = Process(lims, id=process_id)

    pool_lines = []  # save pool data to list, to be able to sort on pool number.

    for pool in process.all_inputs():
        pool_number = int(re.search('Pool #(\d+)_', pool.name).group(1))
        pool_input_artifact = pool.input_artifact_list()[0]

        size = float(pool_input_artifact.udf['Dx Fragmentlengte (bp)'])
        concentration = float(pool_input_artifact.udf['Dx Concentratie fluorescentie (ng/ul)'])
        nM_pool = process.udf['Dx Pool verdunning (nM)']

        nM_dna = (concentration * 1000 * (1/660.0) * (1/size)) * 1000
        ul_sample = (nM_pool/nM_dna) * 20
        ul_EB = 20 - ul_sample

        pool_line = '{pool_name}\t{ul_sample:.2f}\t{ul_EB:.2f}\n'.format(
            pool_name=pool.name,
            ul_sample=ul_sample,
            ul_EB=ul_EB
        )
        pool_lines.append((pool_number, pool_line))

    for pool_number, pool_line in sorted(pool_lines):
        output_file.write(pool_line)


def library_dilution_calculator(concentration, size, trio, pedigree, ng):
# toevoegen ul_sample input en nieuwe berekening toevoegen
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

def samplesheet_multiplex(lims, process_id, output_file):
    """Create manual pipetting samplesheet for multiplexing(pooling) samples."""
    process = Process(lims, id=process_id)
    inputs = process.all_inputs()
    inputs = list(set(inputs))
    sample_concentration = {}
    sample_size = {}
    outputs = process.all_outputs()
    outputs = list(set(outputs))
    trio_statuses = {}
    ul_sample = {}
    ng_sample = {}
    udf_output = []
    udf_ul_sample = {}
    udf_name_ul_sample = {}
    plate_id = {}
    well_id = {}
    not_3 = []
    names = []

    # get input udfs 'Dx sample volume ul' and 'Dx Samplenaam' per output analyte
    for output in outputs:
        if output.type == 'Analyte':
            if 'Dx sample volume (ul)' in output.udf and 'Dx Samplenaam' in output.udf:
                udf_ul_sample[output.name] = output.udf['Dx sample volume (ul)']
                # if samplename is complete sequencename take only monsternummer
                if re.search('U\d\d\d\d\d\d\D\D', output.udf['Dx Samplenaam']):
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

    # get familystatus per sample in output analyte and determine trio composition if number of samples in pool = 3
    for output in outputs:
        if output.type == 'Analyte':
            sample_given_ul = ''
            if len(output.samples) == 3:
                samplestatus_1 = output.samples[0].udf['Dx Familie status']
                samplestatus_2 = output.samples[1].udf['Dx Familie status']
                samplestatus_3 = output.samples[2].udf['Dx Familie status']
                if samplestatus_1 == 'Kind' and samplestatus_2 == 'Kind' and samplestatus_3 == 'Kind' or \
                    samplestatus_1 == 'Ouder' and samplestatus_2 == 'Ouder' and samplestatus_3 == 'Ouder':
                    trio_statuses[output.name] = 'CCC'
                elif samplestatus_1 == 'Kind' and samplestatus_2 == 'Ouder' and samplestatus_3 == 'Ouder' or \
                    samplestatus_1 == 'Ouder' and samplestatus_2 == 'Kind' and samplestatus_3 == 'Ouder' or \
                    samplestatus_1 == 'Ouder' and samplestatus_2 == 'Ouder' and samplestatus_3 == 'Kind': 
                    trio_statuses[output.name] = 'CPP'
                elif samplestatus_1 == 'Kind' and samplestatus_2 == 'Kind' and samplestatus_3 == 'Ouder' or \
                    samplestatus_1 == 'Kind' and samplestatus_2 == 'Ouder' and samplestatus_3 == 'Kind' or \
                    samplestatus_1 == 'Ouder' and samplestatus_2 == 'Kind' and samplestatus_3 == 'Kind':
                    trio_statuses[output.name] = 'CCP'
                # if udfs 'Dx sample volume ul' and 'Dx Samplenaam' are not empty change trio status and do pre-calculation
                if output.name in udf_output:
                    trio_statuses[output.name] = 'adapted'
                    for sample in output.samples:
                        if sample.name == udf_name_ul_sample[output.name]:
                            sample_given_ul = sample
                            ng_sample[sample.name] = \
                                library_dilution_calculator_fixed_volume(sample_concentration[sample.name], \
                                                                         sample_size[sample.name], \
                                                                         udf_ul_sample[output.name]\
                                )
                    for sample in output.samples:
                        if sample.name != udf_name_ul_sample[output.name]:
                            ng_sample[sample.name] = \
                                library_dilution_calculator_fixed_ng(sample_concentration[sample.name], \
                                                                     sample_size[sample.name], \
                                                                     sample.udf['Dx Familie status'], \
                                                                     ng_sample[udf_name_ul_sample[output.name]], \
                                                                     sample_given_ul.udf['Dx Familie status']\
                                )
                    output.udf['Dx input pool (ng)'] = round(ng_sample[output.samples[0].name] + \
                                                             ng_sample[output.samples[1].name] + \
                                                             ng_sample[output.samples[2].name], 2)
                    output.put()
            # if number of samples in pool is not 3 set trio status and prepare error warning output file
            else:
                trio_statuses[output.name] = 'not_3'
                not_3.append(output.name)
            # calculation if udfs 'Dx sample volume ul' and 'Dx Samplenaam' are empty and not empty
            if sample_given_ul == '':
                for sample in output.samples:
                    ul_sample[sample.name] = \
                        library_dilution_calculator(sample_concentration[sample.name], \
                                                    sample_size[sample.name], \
                                                    trio_statuses[output.name], \
                                                    sample.udf['Dx Familie status'], \
                                                    0\
                        )
            elif sample_given_ul != '':
                for sample in output.samples:
                    ul_sample[sample.name] = \
                        library_dilution_calculator(sample_concentration[sample.name], \
                                                    sample_size[sample.name], \
                                                    trio_statuses[output.name], \
                                                    sample.udf['Dx Familie status'], \
                                                    ng_sample[sample.name]\
                        )
            # sorting pools for output file
            name = output.name
            if re.search('#\d_', output.name):
                name = re.sub('#', '#0', output.name)
            names.append(name)
            names = sorted(names)

    # write output file per output analyte sorted on pool number
    output_file.write('Sample\tul Sample\tPlaat_id\twell_id\tpool\n')
    if len(not_3) >= 1:
        output_file.write('De volgende pool(s) hebben een ander aantal samples dan 3: {pools}\n'.format(
            pools=not_3
        ))
    for name in names:
        for output in outputs:
            if output.type == 'Analyte':
                output_name = output.name
                if re.search('#\d_', output.name):
                    output_name = re.sub('#', '#0', output.name)
                if output_name == name:
                    for sample in output.samples:
                        output_file.write('{sample}\t{ul_sample:.2f}\t{plate_id}\t{well_id}\t{pool}\n'.format(
                            sample=sample.name,
                            ul_sample=ul_sample[sample.name],
                            plate_id=plate_id[sample.name],
                            well_id=well_id[sample.name],
                            pool=output.name
                        ))
