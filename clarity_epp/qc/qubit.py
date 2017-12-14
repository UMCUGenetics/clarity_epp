"""Qubit QC epp functions."""

from genologics.entities import Process


def set_qc_flag(lims, process_id, cutoff=10):
    """Set qubit qc flags based on Dx Concentratie fluorescentie (ng/ul) values."""
    process = Process(lims, id=process_id)
    artifacts = process.result_files()
    samples_measurements = {}

    for artifact in artifacts:
        sample = artifact.samples[0]
        measurement = artifact.udf['Dx Conc. goedgekeurde meting (ng/ul)']
        if sample in samples_measurements:
            samples_measurements[sample].append(measurement)
        else:
            samples_measurements[sample] = [measurement]

    for artifact in artifacts:
        sample = artifact.samples[0]
        measurement = artifact.udf['Dx Conc. goedgekeurde meting (ng/ul)']

        sample_measurements = samples_measurements[sample]
        sample_measurements_average = sum(sample_measurements) / float(len(sample_measurements))
        artifact.udf['Dx Concentratie fluorescentie (ng/ul)'] = sample_measurements_average

        cutoff_value = sample_measurements_average * 0.1

        if measurement > (sample_measurements_average - cutoff_value) and measurement < (sample_measurements_average + cutoff_value):
            artifact.qc_flag = 'PASSED'
        else:
            artifact.qc_flag = 'FAILED'
        artifact.put()
