"""Tapestation results upload epp functions."""

from genologics.entities import Process


def results(lims, process_id):
    """Upload tapestation results to artifacts."""
    process = Process(lims, id=process_id)
    sample_size_measurements = {}
    sample_concentration_measurements = {}

    # Parse File
    for output in process.all_outputs(unique=True):
        if output.name == 'TapeStation Output':
            tapestation_result_file = output.files[0]
            for line in lims.get_file_contents(tapestation_result_file.id).split('\n'):
                if line.startswith('FileName'):
                    header = line.split(',')
                    if 'Size [bp]' in header:  # Tapestation compact peak table
                        size_index = header.index('Size [bp]')
                        concentration_index = None
                    else:  # Tapestation compact region table
                        size_index = header.index('Average Size [bp]')
                        try:
                            concentration_index = header.index(u'Conc. [pg/\xb5l]')  # micro sign
                            concentration_correction = 1000  # Used to transform pg/ul to ng/ul
                        except ValueError:
                            concentration_index = header.index(u'Conc. [ng/\xb5l]')  # micro sign
                            concentration_correction = 1
                    sample_index = header.index('Sample Description')

                elif line:
                    data = line.split(',')
                    sample = data[sample_index]
                    if sample != 'Ladder':
                        if data[size_index]:
                            size = int(data[size_index])
                            sample_size_measurements[sample] = size
                        if concentration_index and data[concentration_index]:
                            # Correct concentration
                            concentration = float(data[concentration_index]) / concentration_correction
                            sample_concentration_measurements[sample] = concentration

    # Set UDF
    for artifact in process.all_outputs():
        if artifact.name not in ['TapeStation Output', 'TapeStation Samplesheet', 'TapeStation Sampleplots PDF']:
            sample_name = artifact.name.split('_')[0]
            if sample_name in sample_size_measurements:
                artifact.udf['Dx Fragmentlengte (bp)'] = sample_size_measurements[sample_name]
            if sample_name in sample_concentration_measurements:
                artifact.udf['Dx Concentratie fluorescentie (ng/ul)'] = sample_concentration_measurements[sample_name]
            artifact.put()
