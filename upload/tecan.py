"""Tecan results upload epp functions."""

from genologics.entities import Process
import statsmodels.api as sm


def results(lims, process_id):
    """Upload tecan results to artifacts."""
    process = Process(lims, id=process_id)

    # Parse output file
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
                        coordinate = '{0}{1}'.format(data[0], str(index))
                        if coordinate not in sample_measurements:
                            sample_measurements[coordinate] = {tecan_file_order[tecan_file_part]: float(value)}
                        elif tecan_file_order[tecan_file_part] == 'sample_name':
                            sample_measurements[value] = sample_measurements.pop(coordinate)
                            sample_measurements[value]['coordinate'] = coordinate
                        else:
                            sample_measurements[coordinate][tecan_file_order[tecan_file_part]] = float(value)
                else:
                    tecan_file_part += 1

    # Calculate linear regression for concentration
    baseline_fluorescence = sample_measurements['Dx Tecan std 1']['Dx Fluorescentie (nM)']
    fluorescence_values = [
        sample_measurements['Dx Tecan std 1']['Dx Fluorescentie (nM)'] - baseline_fluorescence,
        sample_measurements['Dx Tecan std 2']['Dx Fluorescentie (nM)'] - baseline_fluorescence,
        sample_measurements['Dx Tecan std 3']['Dx Fluorescentie (nM)'] - baseline_fluorescence,
        sample_measurements['Dx Tecan std 4']['Dx Fluorescentie (nM)'] - baseline_fluorescence,
        sample_measurements['Dx Tecan std 5']['Dx Fluorescentie (nM)'] - baseline_fluorescence,
        sample_measurements['Dx Tecan std 6']['Dx Fluorescentie (nM)'] - baseline_fluorescence,
    ]

    if process.udf['Reagentia kit'] == 'Quant-iT High-Sensitivity dsDNA kit':
        ng_values = [0, 5, 10, 20, 40, 60, 80, 100]
        fluorescence_values.append(sample_measurements['Dx Tecan std 7']['Dx Fluorescentie (nM)'] - baseline_fluorescence)
        fluorescence_values.append(sample_measurements['Dx Tecan std 8']['Dx Fluorescentie (nM)'] - baseline_fluorescence)
    elif process.udf['Reagentia kit'] == 'Quant-iT Broad Range dsDNA kit':
        ng_values = [0, 50, 100, 200, 400, 600]

    regression_model = sm.OLS(ng_values, fluorescence_values)
    regression_result = regression_model.fit()

    regression_slope = regression_result.params[0]

    # Set udf values
    for artifact in process.all_outputs():
        if artifact.name != 'Tecan Spark Output' and artifact.name != 'Tecan Spark Samplesheet':
            sample_fluorescence = sample_measurements[artifact.name]['Dx Fluorescentie (nM)']
            sample_concentration = ((sample_fluorescence - baseline_fluorescence) * regression_slope) / 2.0

            artifact.udf['Dx Fluorescentie (nM)'] = sample_fluorescence
            artifact.udf['Dx Concentratie fluorescentie (ng/ul)'] = sample_concentration
            artifact.put()
