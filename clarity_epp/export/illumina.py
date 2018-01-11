"""Illumina export functions."""
from genologics.entities import Process


def update_samplesheet(lims, process_id, file_id, output_file):
    """Update illumina samplesheet."""
    process = Process(lims, id=process_id)
    sample_project = {}
    for artifact in process.all_inputs():
        for sample in artifact.samples:
            if sample.udf['Dx NICU Spoed']:
                sample_project[sample.name] = 'NICU_{fam}'.format('Dx Familienummer')
            elif sample.udf['Dx Protocolomschrijving'] == 'Exoom.analy_IL_elidS30409818_Exoomver.':
                sample_project[sample.name] = 'CREv2'
            else:
                sample_project[sample.name] = 'Unkown_project'

    header = ''  # empty until [data] section

    for line in lims.get_file_contents(id=file_id).rstrip().split('\n'):
        if line.startswith('Sample_ID'):
            header = line.rstrip().split(',')
            output_file.write('{line}\n'.format(line=line))
        elif header:
            data = line.rstrip().split(',')
            sample_name_index = header.index('Sample_Name')
            sample_project_index = header.index('Sample_Project')

            sample_name = data[sample_name_index][9:]
            data[sample_project_index] = sample_project[sample_name]
            output_file.write('{line}\n'.format(line=','.join(data)))
        else:
            output_file.write('{line}\n'.format(line=line))
