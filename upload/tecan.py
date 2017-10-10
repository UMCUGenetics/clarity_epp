"""Tecan results upload epp functions."""

from genologics.entities import Process


def results(lims, process_id):
    """Upload tecan results to artifacts."""
    process = Process(lims, id=process_id)
    for output in process.shared_result_files():
        if output.name == 'Tecan Spark Output':
            tecan_result_file = output.files[0]
            tecan_file_order = ['Dx Fluorescentie (nM)', 'Dx Concentratie fluorescentie (ng/ul)', 'sample_name']
            tecan_file_part = -1

            sample_measurements = {}

            for line in lims.get_file_contents(tecan_result_file.id).split('\n'):

                if not line.startswith('<>'):
                    data = line.rstrip().split('\t')
                    for index, value in enumerate(data[1:]):
                        coordinate = '{}{}'.format(data[0], str(index))
                        if coordinate not in sample_measurements:
                            sample_measurements[coordinate] = {tecan_file_order[tecan_file_part]: float(value)}
                        elif tecan_file_order[tecan_file_part] == 'sample_name':
                            sample_measurements[value] = sample_measurements.pop(coordinate)
                            sample_measurements[value]['coordinate'] = coordinate
                        else:
                            sample_measurements[coordinate][tecan_file_order[tecan_file_part]] = float(value)
                else:
                    tecan_file_part += 1

    for artifact in process.all_outputs():
        if artifact.name != 'Tecan Spark Output' and artifact.name != 'Tecan Spark Samplesheet':
            artifact.udf['Dx Fluorescentie (nM)'] = sample_measurements[artifact.name]['Dx Fluorescentie (nM)']
            artifact.udf['Dx Concentratie fluorescentie (ng/ul)'] = sample_measurements[artifact.name]['Dx Concentratie fluorescentie (ng/ul)']
            artifact.put()
