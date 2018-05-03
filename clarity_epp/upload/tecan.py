"""Tecan results upload epp functions."""

from genologics.entities import Process


def results(lims, process_id):
    """Upload tecan results to artifacts."""
    process = Process(lims, id=process_id)

    # Parse output file
    for output in process.result_files():
        if output.name == 'Tecan Spark Output':
            tecan_result_file = output.files[0]
            tecan_file_order = ['Dx Fluorescentie (nM)', 'sample_name']
            tecan_file_part = -1

            measurements = {}
            sample_measurements = {}
            for line in lims.get_file_contents(tecan_result_file.id).data.split('\n'):
                if not line.startswith('<>'):
                    data = line.rstrip().split('\t')
                    for index, value in enumerate(data[1:]):
                        value = value.rstrip()
                        if value:
                            coordinate = '{0}{1}'.format(data[0], str(index))
                            if tecan_file_order[tecan_file_part] == 'Dx Fluorescentie (nM)':
                                measurements[coordinate] = float(value)

                            elif tecan_file_order[tecan_file_part] == 'sample_name':
                                if value not in sample_measurements:
                                    sample_measurements[value] = [measurements[coordinate]]
                                else:
                                    sample_measurements[value].append(measurements[coordinate])
                else:
                    tecan_file_part += 1
    # Calculate linear regression for concentration
    # Assumes no std duplicates
    baseline_fluorescence = sample_measurements['Dx Tecan std 1'][0]
    fluorescence_values = [
        sample_measurements['Dx Tecan std 1'][0] - baseline_fluorescence,
        sample_measurements['Dx Tecan std 2'][0] - baseline_fluorescence,
        sample_measurements['Dx Tecan std 3'][0] - baseline_fluorescence,
        sample_measurements['Dx Tecan std 4'][0] - baseline_fluorescence,
        sample_measurements['Dx Tecan std 5'][0] - baseline_fluorescence,
        sample_measurements['Dx Tecan std 6'][0] - baseline_fluorescence,
    ]

    if process.udf['Reagentia kit'] == 'Quant-iT High-Sensitivity dsDNA kit':
        ng_values = [0, 5, 10, 20, 40, 60, 80, 100]
        fluorescence_values.append(sample_measurements['Dx Tecan std 7'][0] - baseline_fluorescence)
        fluorescence_values.append(sample_measurements['Dx Tecan std 8'][0] - baseline_fluorescence)
    elif process.udf['Reagentia kit'] == 'Quant-iT Broad Range dsDNA kit':
        ng_values = [0, 50, 100, 200, 400, 600]

    regression_slope = sum([x*y for x, y in zip(fluorescence_values, ng_values)]) / sum([x**2 for x in fluorescence_values])
    rsquared = 1 - (sum([(y - x*regression_slope)**2 for x, y in zip(fluorescence_values, ng_values)]) / sum([y**2 for y in ng_values]))

    # Set udf values
    process.udf['R-squared waarde'] = rsquared
    process.put()
    artifact_count = {}

    for artifact in process.all_outputs():
        if artifact.name not in ['Tecan Spark Output', 'Tecan Spark Samplesheet', 'check gemiddelde concentratie']:
            # Set Average Concentratie fluorescentie
            sample_fluorescence = sum(sample_measurements[artifact.name]) / float(len(sample_measurements[artifact.name]))
            sample_concentration = ((sample_fluorescence - baseline_fluorescence) * regression_slope) / 2.0
            artifact.udf['Dx Concentratie fluorescentie (ng/ul)'] = sample_concentration

            # Set artifact Concentratie fluorescentie
            # Get artifact index == count
            if artifact.name not in artifact_count:
                artifact_count[artifact.name] = 0
            else:
                artifact_count[artifact.name] += 1

            artifact_fluorescence = sample_measurements[artifact.name][artifact_count[artifact.name]]
            artifact_concentration = ((artifact_fluorescence - baseline_fluorescence) * regression_slope) / 2.0
            artifact.udf['Dx Conc. goedgekeurde meting (ng/ul)'] = artifact_concentration

            # Set QC flags
            if artifact.name.startswith('Dx Tecan std'):
                artifact.qc_flag = 'PASSED'
            else:
                cutoff_value = sample_concentration * 0.1
                if artifact_concentration > (sample_concentration - cutoff_value) and artifact_concentration < (sample_concentration + cutoff_value):
                    artifact.qc_flag = 'PASSED'
                else:
                    artifact.qc_flag = 'FAILED'
            artifact.put()
