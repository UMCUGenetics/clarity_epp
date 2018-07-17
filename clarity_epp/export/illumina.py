"""Illumina export functions."""
import re

from genologics.entities import Process, Artifact


def update_samplesheet(lims, process_id, artifact_id, output_file):
    """Update illumina samplesheet."""
    process = Process(lims, id=process_id)

    # Parse families
    families = {}
    for artifact in process.all_inputs():
        for sample in artifact.samples:
            family = sample.udf['Dx Familienummer']
            sample_name = sample.name

            if family not in families:
                if sample.udf['Dx NICU Spoed']:
                    project_type = 'NICU_{0}'.format(sample.udf['Dx Familienummer'])
                elif 'elidS30409818' in sample.udf['Dx Protocolomschrijving']:
                    project_type = 'CREv2'
                else:
                    project_type = 'Unkown_project'
                families[family] = {'samples': [], 'project_type': project_type, 'nicu': sample.udf['Dx NICU Spoed']}
            families[family]['samples'].append(sample)

    # Define projects
    sample_project = {}
    projects = {
        'CREv2': {'count': 1, 'samples': 0},
        'Unkown_project': {'count': 1, 'samples': 0}
    }

    for i, family in families.iteritems():
        if family['nicu']:
            family_project = family['project_type']
        else:
            if projects[family['project_type']]['samples'] + len(family['samples']) <= 9:
                projects[family['project_type']]['samples'] += len(family['samples'])
            else:
                projects[family['project_type']]['count'] += 1
                projects[family['project_type']]['samples'] = len(family['samples'])
            family_project = '{0}_{1}'.format(family['project_type'], projects[family['project_type']]['count'])

        # Set samples project
        for sample in family['samples']:
            sample_project[sample.name] = family_project

    header = ''  # empty until [data] section

    samplesheet_artifact = Artifact(lims, id=artifact_id)
    file_id = samplesheet_artifact.files[0].id
    for line in lims.get_file_contents(id=file_id).rstrip().split('\n'):
        if line.startswith('Sample_ID'):
            header = line.rstrip().split(',')
            output_file.write('{line}\n'.format(line=line))
        elif header:
            data = line.rstrip().split(',')
            sample_id_index = header.index('Sample_ID')
            sample_name_index = header.index('Sample_Name')
            sample_project_index = header.index('Sample_Project')

            # Set Sample_Project
            sample_name = re.search('^U\d+[CP][MFO](\w+)$', data[sample_name_index]).group(1)
            data[sample_project_index] = sample_project[sample_name]

            # Overwrite Sample_ID with Sample_name to get correct conversion output folder structure
            data[sample_id_index] = data[sample_name_index]

            output_file.write('{line}\n'.format(line=','.join(data)))
        else:
            output_file.write('{line}\n'.format(line=line))
