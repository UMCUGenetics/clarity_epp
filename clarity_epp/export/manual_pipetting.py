"""Manual pipetting export functions."""

from genologics.entities import Process
import datetime


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
    for pool in process.all_inputs():

        size = float(pool.udf['Dx Fragmentlengte (bp)'])
        concentration = float(pool.udf['Dx Concentratie fluorescentie (ng/ul)'])

        nM_dna = (concentration * 1000 * (1/649.0) * (1/size)) * 1000
        ul_sample = (2/nM_dna) * 20
        ul_EB = 20 - ul_sample

        output_file.write('{pool_name}\t{ul_sample:.2f}\t{ul_EB:.2f}\n'.format(
            pool_name=pool.name,
            ul_sample=ul_sample,
            ul_EB=ul_EB
        ))


def library_dilution_calculator(concentration, size, pedigree, factor):
    """Calculate ul per sample needed for multiplexing."""
    ul_sample = []
    ng_sample = []

    nM_DNA = (float(concentration)*(10.0**3.0)*(1.0/649.0)*(1.0/float(size)))*1000.0
    if pedigree == 'Child':
        ul_sample = (float(factor)/nM_DNA)*11.0
    if pedigree == 'Parent':
        ul_sample = (float(factor)/nM_DNA)*10.0
    ng_sample = float(concentration)*ul_sample
    return ul_sample, ng_sample


def samplesheet_multiplex(lims, process_id, output_file):
    """Create manual pipetting samplesheet for multiplexing(pooling) samples."""
    output_file.write('Sample\tul Sample\tPlaat_id\twell_id\tpool\n')
    process = Process(lims, id=process_id)
    parent_process = []
    parent_process = process.parent_processes()
    parent_process = list(set(parent_process))
    input_artifact_ids = []
    for p in parent_process:
        for analyte in p.all_outputs():
            input_artifact_ids.append(analyte.id)
    input_artifact_ids = list(set(input_artifact_ids))
    qc_processes = lims.get_processes(
        type=['Dx Qubit QC', 'Dx Tecan Spark 10M QC', 'Dx Bioanalyzer QC', 'Dx Tapestation 2200 QC', 'Dx Tapestation 4200 QC'],
        inputartifactlimsid=input_artifact_ids
    )
    samples_measurements_tecan = {}
    samples_measurements_qubit = {}
    sample_concentration = {}
    samples_measurements_tapestation = {}
    samples_measurements_bioanalyzer = {}
    sample_size = {}
    Unummers_per_monster = {}
    years = {}
    genders = {}
    parent_parent_process = []
    for p in parent_process:
        for pp in p.parent_processes():
            parent_parent_process.append(pp)
    parent_parent_process = list(set(parent_parent_process))
    family_status = {}
    samplenamen = {}
    pool_per_monsternummer = {}
    ul_per_monsternummer = {}
    well = {}
    plate_per_monsternummer = {}

    for p in qc_processes:
        for a in p.all_outputs():
            if 'Dx Concentratie fluorescentie (ng/ul)' in a.udf:
                if 'Tecan' in a.parent_process.type.name:
                    machine = 'Tecan'
                    sample = a.samples[0].name
                    measurement = a.udf['Dx Concentratie fluorescentie (ng/ul)']
                    qcflag = a.qc_flag
                    if qcflag == 'UNKNOWN' or 'PASSED':
                        if sample in samples_measurements_tecan:
                            samples_measurements_tecan[sample].append(measurement)
                        else:
                            samples_measurements_tecan[sample] = [measurement]
                elif 'Qubit' in a.parent_process.type.name:
                    machine = 'Qubit'
                    sample = a.samples[0].name
                    measurement = a.udf['Dx Concentratie fluorescentie (ng/ul)']
                    qcflag = a.qc_flag
                    if qcflag == 'PASSED':
                        if sample in samples_measurements_qubit:
                            samples_measurements_qubit[sample].append(measurement)
                        else:
                            samples_measurements_qubit[sample] = [measurement]
                if sample not in sample_concentration or machine == 'Qubit':
                    if machine == 'Tecan':
                        sample_measurements = samples_measurements_tecan[sample]
                    elif machine == 'Qubit':
                        sample_measurements = samples_measurements_qubit[sample]
                    sample_measurements_average = sum(sample_measurements) / float(len(sample_measurements))
                    sample_concentration[sample] = sample_measurements_average
            if 'Dx Fragmentlengte (bp)' in a.udf:
                if 'Tapestation' in a.parent_process.type.name:
                    machine = 'Tapestation'
                    sample = a.samples[0].name
                    measurement = a.udf['Dx Fragmentlengte (bp)']
                    qcflag = a.qc_flag
                    if qcflag == 'UNKNOWN' or 'PASSED':
                        if sample in samples_measurements_tapestaion:
                            samples_measurements_tapestation[sample].append(measurement)
                        else:
                            samples_measurements_tapestation[sample] = [measurement]
                elif 'Bioanalyzer' in a.parent_process.type.name:
                    machine = 'Bioanalyzer'
                    sample = a.samples[0].name
                    measurement = a.udf['Dx Fragmentlengte (bp)']
                    qcflag = a.qc_flag
                    if qcflag == 'UNKNOWN' or 'PASSED':
                        if sample in samples_measurements_bioanalyzer:
                            samples_measurements_bioanalyzer[sample].append(measurement)
                        else:
                            samples_measurements_bioanalyzer[sample] = [measurement]
                if sample not in sample_size or machine == 'Bioanalyzer':
                    if machine == 'Tapestation':
                        sample_measurements = samples_measurements_tapestation[sample]
                    elif machine == 'Bioanalyzer':
                        sample_measurements = samples_measurements_bioanalyzer[sample]
                    sample_measurements_average = sum(sample_measurements) / float(len(sample_measurements))
                    sample_size[sample] = sample_measurements_average

    for p in parent_process:
        plate = p.output_containers()[0].name
        for placement, artifact in p.output_containers()[0].placements.iteritems():
            sample = artifact.samples[0]
            monsternummer = sample.name
            plate_per_monsternummer[monsternummer] = plate
            Unummers_per_monster[monsternummer] = sample.udf['Dx Unummer']

            if sample.udf['Dx Geslacht'].lower() == 'man':
                genders[monsternummer] = 'M'
            elif sample.udf['Dx Geslacht'].lower() == 'vrouw':
                genders[monsternummer] = 'F'
            elif sample.udf['Dx Geslacht'].lower() == 'onbekend':
                genders[monsternummer] = 'O'

            if sample.udf['Dx Foetus']:
                years[monsternummer] = datetime.datetime.now().year
            else:
                years[monsternummer] = sample.udf['Dx Geboortejaar']

    for pp in parent_parent_process:
        for placement, artifact in pp.output_containers()[0].placements.iteritems():
            sample = artifact.samples[0]
            monsternummer = sample.name
            family_status[monsternummer] = sample.udf['Dx Familie status']

    for p in parent_process:
        for placement, artifact in p.output_containers()[0].placements.iteritems():
            monsternummer = artifact.samples[0].name
            if family_status[monsternummer] == 'Kind':
                pedigree = 'C'
            elif family_status[monsternummer] == 'Ouder':
                pedigree = 'P'
            #elif family_status[monsternummer] == 'Unknown':
            #    pedigree = 'C'
            samplenaam = "%s%s%s%s" % (Unummers_per_monster[monsternummer], pedigree, genders[monsternummer], monsternummer)
            samplenamen[monsternummer] = samplenaam

    for container in process.output_containers():
        artifact = container.placements['1:1']
        pool = artifact.name
        ng_samples = []
        if len(artifact.samples) == 3:
            factor = 80
            ng_samples.append(850.0)
            while (sum(ng_samples) > 800.0):
                ng_samples = []
                for sample in artifact.samples:
                    monsternummer = sample.name
                    pool_per_monsternummer[monsternummer] = pool
                    average_concentration = sample_concentration[monsternummer]
                    average_size = sample_size[monsternummer]
                    pedigree = family_status[monsternummer]
                    ul_sample, ng_sample = library_dilution_calculator(average_concentration, average_size, pedigree, factor)
                    if ul_sample < 25:
                        if ul_sample > 23:
                            pool_per_monsternummer[monsternummer] = "%s let op!: ul sample 23-25" % pool
                        ul_per_monsternummer[monsternummer] = ul_sample
                        ng_samples.append(ng_sample)
                    elif ul_sample > 25:
                        ul_per_monsternummer[monsternummer] = 0.0
                        pool_per_monsternummer[monsternummer] = "%s error: ul sample > 25" % pool
                factor = factor - 5
            if sum(ng_samples) < 650:
                output_file.write('Let op! De volgende pool heeft een totaal aantal ng < 650: {pool} (Mogelijke oorzaak is error ul sample > 25, zie {pool} hieronder.)\n'.format(
                    pool=pool
                ))
        else:
            for sample in artifact.samples:
                monsternummer = sample.name
                pool_per_monsternummer[monsternummer] = "%s error: geen 3 samples in deze pool" % pool
                ul_per_monsternummer[monsternummer] = 0.0

    for p in parent_process:
        for placement, artifact in p.output_containers()[0].placements.iteritems():
            monsternummer = artifact.samples[0].name
            placement = ''.join(placement.split(':'))
            well[monsternummer] = placement

    for container in process.output_containers():
        artifact = container.placements['1:1']
        for sample in artifact.samples:
            monsternummer = sample.name
            output_file.write('{sample}\t{ul_sample:.1f}\t{plate_id}\t{well_id}\t{pool}\n'.format(
                sample=samplenamen[monsternummer],
                ul_sample=ul_per_monsternummer[monsternummer],
                plate_id=plate_per_monsternummer[monsternummer],
                well_id=well[monsternummer],
                pool=pool_per_monsternummer[monsternummer]
            ))
