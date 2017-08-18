"""Manual pipetting epp functions."""

from genologics.entities import Process


def purify(lims, process_id, output_file):
    """Create manual pipetting samplesheet for purifying samples."""
    with open(output_file, 'w') as file:
        file.write('Fractienummer\tConcentration(ng/uL)\taantal ng te isoleren\tuL gDNA\tuL Water\n')
        process = Process(lims, id=process_id)

        for container in process.output_containers():
            artifact = container.placements['1:1']  # asume tubes
            input_artifact = artifact.input_artifact_list()[0]  # asume one input artifact
            sample = artifact.samples[0]  # asume one sample per tube

            fractienummer = sample.udf['Dx Fractienummer']

            if 'Dx Concentratie fluorescentie (ng/uL)' in input_artifact.udf:
                    concentration = input_artifact.udf['Dx Concentratie fluorescentie (ng/uL)']
            elif 'Dx Concentratie OD (ng/uL)' in input_artifact.udf:
                    concentration = input_artifact.udf['Dx Concentratie OD (ng/uL)']
            elif 'Dx Concentratie (ng/uL)' in sample.udf:
                    concentration = sample.udf['Dx Concentratie (ng/uL)']

            input_gdna_ng = artifact.udf['Dx input hoevelheid (ng)']
            uL_gdna = input_gdna_ng/concentration
            uL_water = 200 - uL_gdna

            file.write('{fractienummer}\t{concentration}\t{input_gdna_ng}\t{uL_gdna}\t{uL_water}\n'.format(
                fractienummer=fractienummer,
                concentration=concentration,
                input_gdna_ng=input_gdna_ng,
                uL_gdna=uL_gdna,
                uL_water=uL_water
            ))
