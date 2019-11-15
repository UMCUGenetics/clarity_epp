"""Qubit QC epp functions."""

import re

from genologics.entities import Process


def set_qc_flag(lims, process_id, cutoff=10):
    """Set qubit qc flags based on Dx Concentratie fluorescentie (ng/ul) values."""
    process = Process(lims, id=process_id)
    artifacts = process.result_files()
    samples_measurements = {}

    concentration_range = map(int, re.findall('[\d]+', process.udf['Concentratiebereik (ng/ul)']))

    for artifact in artifacts:
        sample = artifact.name.rstrip('Qubit').rstrip()
        measurement = artifact.udf['Dx Conc. goedgekeurde meting (ng/ul)']
        if sample in samples_measurements:
            samples_measurements[sample].append(measurement)
        else:
            samples_measurements[sample] = [measurement]

    for artifact in artifacts:
        sample = artifact.name.rstrip('Qubit').rstrip()

        sample_measurements = samples_measurements[sample]
        sample_measurements_average = sum(sample_measurements) / float(len(sample_measurements))
        artifact.udf['Dx Concentratie fluorescentie (ng/ul)'] = sample_measurements_average

        if concentration_range[0] <= sample_measurements_average <= concentration_range[1]:
            if len(sample_measurements) == 1:
                artifact.qc_flag = 'PASSED'
            elif len(sample_measurements) == 2:
                sample_measurements_difference = abs(sample_measurements[0] - sample_measurements[1])
                sample_measurements_deviation = sample_measurements_difference / sample_measurements_average
                if sample_measurements_deviation <= 0.1:
                    artifact.qc_flag = 'PASSED'
                else:
                    artifact.qc_flag = 'FAILED'
        else:
            artifact.qc_flag = 'FAILED'

        artifact.put()
