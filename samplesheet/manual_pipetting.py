"""Manual pipetting epp functions."""

from genologics.entities import Process


def purify(lims, process_id, output_file):
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


def sequencing_pool(lims, process_id, output_file):
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
