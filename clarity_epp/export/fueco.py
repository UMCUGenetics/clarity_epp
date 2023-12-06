from genologics.entities import Process

import clarity_epp.export.utils


def samplesheet(lims, process_id, output_file):
    """Create Fueco - pipetting assistence samplesheet."""

    output_file.write('Monsternummer,Well,Plate_Id_output,Pipetteervolume DNA (ul),Pipetteervolume H2O (ul),Plate_Id_input\n')
    process = Process(lims, id=process_id)
    well_plate = {}

    output_container = process.output_containers()[0]
    # input_containers = {artifact.name: artifact.container.name for artifact in process.all_inputs(unique=True)}

    qc_process_types = clarity_epp.export.utils.get_process_types(lims, ['Dx Qubit QC', 'Dx Tecan Spark 10M QC'])

    for placement, artifact in output_container.placements.items():
        placement = ''.join(placement.split(':'))
        well_plate[placement] = {'samples': [], 'containers': [], 'volume_dna': []}

        if len(artifact.samples) == 1:
            input_artifacts = [artifact.input_artifact_list()[0]]
        else:
            input_artifacts = artifact.input_artifact_list()[0].input_artifact_list()

        for input_artifact in input_artifacts:
            # Find last qc process for artifact
            qc_process = lims.get_processes(type=qc_process_types, inputartifactlimsid=input_artifact.id)
            concentration = None
            if qc_process:
                qc_process = sorted(
                    qc_process,
                    key=lambda process: int(process.id.split('-')[-1])
                )[-1]
                for qc_artifact in qc_process.outputs_per_input(input_artifact.id):
                    if input_artifact.name in qc_artifact.name:
                        concentration = float(qc_artifact.udf['Dx Concentratie fluorescentie (ng/ul)'])
                        break

            if not concentration:
                concentration = input_artifact.samples[0].udf['Dx Concentratie (ng/ul)']

            # Calculate volumes
            volume_dna = (artifact.udf['Dx input hoeveelheid (ng)']/len(input_artifacts)) / concentration
            well_plate[placement]['samples'].append(input_artifact.samples[0].udf['Dx Monsternummer'])
            well_plate[placement]['containers'].append(input_artifact.container.name)
            well_plate[placement]['volume_dna'].append(volume_dna)

    for well in clarity_epp.export.utils.sort_96_well_plate(well_plate.keys()):
        volume_h2o = 40 - sum(well_plate[well]['volume_dna'])
        if volume_h2o < 0:  # Set volume_h2o to 0 if negative
            volume_h2o = 0

        for index, sample in enumerate(well_plate[well]['samples']):
            output_file.write('{name},{well},{plate_id_output},{volume_dna:.2f},{volume_h2o:.2f},{plate_id_input}\n'.format(
                name=sample,
                well=well,
                plate_id_output=output_container.name,
                volume_dna=well_plate[well]['volume_dna'][index],
                volume_h2o=volume_h2o,
                plate_id_input=well_plate[well]['containers'][index]
            ))
