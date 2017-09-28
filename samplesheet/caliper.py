"""Caliper samplesheet epp functions."""

from genologics.entities import Process, SampleHistory, Processtype

import utils


def normalise(lims, process_id, output_file):
    """Create Caliper samplesheet for normalising 96 well plate."""
    output_file.write('Monsternummer\tPlate_Id_input\tWell\tPlate_Id_output\tPipetteervolume DNA (ul)\tPipetteervolume H2O (ul)\n')
    process = Process(lims, id=process_id)
    parent_process = process.parent_processes()[0]

    parent_process_barcode = parent_process.output_containers()[0].name
    output_plate_barcode = process.output_containers()[0].name
    monsternummer = {}
    conc = {}
    conc_measured = {}
    volume_DNA = {}
    volume_H2O = {}
    output_ng = process.udf['Output genormaliseerd gDNA']
    output_ul = process.udf['Eindvolume (ul) genormaliseerd gDNA']

    input_artifact_ids = [analyte.id for analyte in parent_process.all_outputs()]
    qc_processes = lims.get_processes(
        type=['Dx Qubit QC', 'Dx Tecan Spark 10M QC'],
        inputartifactlimsid=input_artifact_ids
    )

    sample_concentration = {}
    for p in qc_processes:
        for a in p.all_outputs():
            if 'Dx Concentratie fluorescentie (ng/ul)' in a.udf:
                sample, machine = a.name.split(' ')
                if sample not in sample_concentration or machine == 'Qubit':
                    sample_concentration[sample] = a.udf['Dx Concentratie fluorescentie (ng/ul)']

    for placement, artifact in process.output_containers()[0].placements.iteritems():
        sample = artifact.samples[0].name
        placement = ''.join(placement.split(':'))
        monsternummer[placement] = sample
        conc_measured[placement] = sample_concentration[sample]

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
