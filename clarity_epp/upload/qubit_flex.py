"""Qubit Flex results upload epp functions."""

from genologics.entities import Process


def results_array(lims, process_id):
    """Fill Dx Concentratie fluorescentie (ng/ul) udf with values from uploaded file."""
    process = Process(lims, id=process_id)
    concentration_measurements = {}
    sample_concentration = {}

    # Parse File
    for output in process.all_outputs(unique=True):
        if output.name == 'Qubit Flex output':
            qubit_flex_result_file = output.files[0]
            for line in lims.get_file_contents(qubit_flex_result_file.id).split('\n'):
                if line.startswith('Run ID'):
                    header = line.split(',')
                    concentration_index = header.index(u'Original Sample Conc.')
                    sample_index = header.index('Sample Name')

                elif line:
                    data = line.split(',')
                    sample = data[sample_index]
                    if concentration_index and data[concentration_index]:
                        concentration = float(data[concentration_index])
                        concentration_measurements[sample] = concentration

    # Qubit Flex sample to well translation
    translation_dict = {
        'A1':'S1','B1':'S2','C1':'S3','D1':'S4','E1':'S5','F1':'S6','G1':'S7','H1':'S8',
        'A2':'S9','B2':'S10','C2':'S11','D2':'S12','E2':'S13','F2':'S14','G2':'S15','H2':'S16'}

    for artifact in process.all_inputs():
        well = ''.join(artifact.location[1].split(':'))
        sample = translation_dict[well]
        sample_concentration[artifact.name] = concentration_measurements[sample]

    # Set UDF
    for artifact in process.all_outputs():
        if artifact.name not in ['Qubit Flex output']:
            if artifact.name in sample_concentration:
                artifact.udf['Dx Concentratie fluorescentie (ng/ul)'] = sample_concentration[artifact.name]
            artifact.put()