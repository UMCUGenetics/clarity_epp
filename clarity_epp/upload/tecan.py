"""Tecan results upload epp functions."""

import re

from genologics.entities import Process

from clarity_epp.upload.utils import txt_to_bool


def results_qc(lims, process_id):
    """Upload tecan results to artifacts."""
    process = Process(lims, id=process_id)
    concentration_range = list(map(float, re.findall('[\d\.]+', process.udf['Concentratiebereik (ng/ul)'])))

    # Parse output file
    for output in process.all_outputs(unique=True):
        if output.name == 'Tecan Spark Output':
            tecan_result_file = output.files[0]
            tecan_file_order = ['Dx Fluorescentie (nM)', 'sample_name']
            tecan_file_part = -1

            measurements = {}
            sample_measurements = {}
            for line in str(lims.get_file_contents(tecan_result_file.id).data, encoding='utf-8').split('\n'):
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
        if artifact.name not in ['Tecan Spark Output', 'Tecan Spark Samplesheet', 'check gemiddelde concentratie', 'Label plaat']:
            if len(artifact.samples) == 1:  # Remove 'meet_id' from artifact name if artifact is not a pool
                artifact_name = artifact.name.split('_')[0]
            else:
                artifact_name = artifact.name

            # Set Average Concentratie fluorescentie
            sample_fluorescence = sum(sample_measurements[artifact_name]) / float(len(sample_measurements[artifact_name]))
            sample_concentration = ((sample_fluorescence - baseline_fluorescence) * regression_slope) / 2.0
            artifact.udf['Dx Concentratie fluorescentie (ng/ul)'] = sample_concentration

            # Reset 'Dx norm. manueel' udf
            if 'Dx Tecan std' not in artifact.name:
                for analyte in process.analytes()[0]:
                    if analyte.name == artifact.name:
                        if 'Dx Sample registratie zuivering' in analyte.parent_process.type.name:
                            if sample_concentration <= 29.3:
                                artifact.samples[0].udf['Dx norm. manueel'] = True
                            else:
                                artifact.samples[0].udf['Dx norm. manueel'] = False
                            artifact.samples[0].put()

            # Set artifact Concentratie fluorescentie
            # Get artifact index == count
            if artifact_name not in artifact_count:
                artifact_count[artifact_name] = 0
            else:
                artifact_count[artifact_name] += 1

            artifact_fluorescence = sample_measurements[artifact_name][artifact_count[artifact_name]]
            artifact_concentration = ((artifact_fluorescence - baseline_fluorescence) * regression_slope) / 2.0
            artifact.udf['Dx Conc. goedgekeurde meting (ng/ul)'] = artifact_concentration

            # Set QC flags
            if artifact_name.startswith('Dx Tecan std'):
                artifact.qc_flag = 'PASSED'
                std_number = int(artifact_name.split(' ')[3])
                artifact.udf['Dx Conc. goedgekeurde meting (ng/ul)'] = ng_values[std_number - 1]
                artifact.udf['Dx Concentratie fluorescentie (ng/ul)'] = ng_values[std_number - 1]
            else:
                # Calculate measurement deviation from average.
                if concentration_range[0] <= sample_concentration <= concentration_range[1]:
                    if len(sample_measurements[artifact_name]) == 1:
                        artifact.qc_flag = 'PASSED'
                    elif len(sample_measurements[artifact_name]) == 2:
                        artifact_fluorescence_difference = abs(sample_measurements[artifact_name][0] - sample_measurements[artifact_name][1])
                        artifact_fluorescence_deviation = artifact_fluorescence_difference / sample_fluorescence
                        if artifact_fluorescence_deviation <= 0.1:
                            artifact.qc_flag = 'PASSED'
                        else:
                            artifact.qc_flag = 'FAILED'
                else:
                    artifact.qc_flag = 'FAILED'

            artifact.put()


def results_purify_normalise(lims, process_id):
    """Upload tecan results to artifacts."""
    process = Process(lims, id=process_id)

    # Find and parse Tecan Fluent 480 Output
    tecan_result = {}
    for result_file in process.result_files():
        if result_file.name == 'Tecan Fluent 480 Output':
            file_data = lims.get_file_contents(result_file.files[0].id).split('\n')
            header = file_data[0].rstrip().split(';')
            for line in file_data[1:]:
                if line.rstrip():
                    data = line.rstrip().split(';')
                    tecan_result[data[header.index('SampleID')]] = {
                        'conc': float(data[header.index('Concentratie(ng/ul)')]),
                        'norm': txt_to_bool(data[header.index('Normalisatie')])
                    }
            break  # File found exit loop

    # Set concentration values on artifacts
    for artifact in process.analytes()[0]:
        sample = artifact.samples[0]  # assume one sample per artifact
        artifact.udf['Dx Concentratie fluorescentie (ng/ul)'] = tecan_result[sample.udf['Dx Fractienummer']]['conc']
        artifact.udf['Dx QC status'] = tecan_result[sample.udf['Dx Fractienummer']]['norm']
        artifact.put()


def results_purify_mix(lims, process_id):
    """Upload tecan results to artifacts (mix samples)."""
    process = Process(lims, id=process_id)

    # Find and parse Tecan Fluent 480 Output
    tecan_result = {}
    for result_file in process.result_files():
        if result_file.name == 'Tecan Fluent 480 Output':
            file_data = lims.get_file_contents(result_file.files[0].id).split('\n')
            header = file_data[0].rstrip().split(';')
            for line in file_data[1:]:
                if line.rstrip():
                    data = line.rstrip().split(';')
                    tecan_result[data[header.index('SampleID')]] = {
                        'conc': float(data[header.index('Concentratie(ng/ul)')]),
                        'norm': txt_to_bool(data[header.index('Normalisatie')])
                    }
            break  # File found exit loop

    # Set concentration values on artifacts
    for artifact in process.analytes()[0]:
        if len(artifact.samples) > 1:
            artifact.udf['Dx Concentratie fluorescentie (ng/ul)'] = tecan_result[artifact.name]['conc']
            artifact.udf['Dx QC status'] = tecan_result[artifact.name]['norm']
        else:
            sample = artifact.samples[0]
            artifact.udf['Dx Concentratie fluorescentie (ng/ul)'] = tecan_result[sample.udf['Dx Monsternummer']]['conc']
            artifact.udf['Dx QC status'] = tecan_result[sample.udf['Dx Monsternummer']]['norm']
        artifact.put()
