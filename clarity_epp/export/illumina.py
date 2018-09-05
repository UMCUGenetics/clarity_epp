"""Illumina export functions."""
import re

from genologics.entities import Process, Artifact

from .. import get_sequence_name


def update_samplesheet(lims, process_id, artifact_id, output_file):
    """Update illumina samplesheet."""
    process = Process(lims, id=process_id)

    # Parse families
    families = {}
    for artifact in process.all_inputs():
        for sample in artifact.samples:
            if 'Dx Familienummer' in list(sample.udf) and 'Dx NICU Spoed' in list(sample.udf) and 'Dx Protocolomschrijving' in list(sample.udf):
                # Dx sample
                family = sample.udf['Dx Familienummer']
                # Create family if not exist
                if family not in families:
                    families[family] = {'samples': [], 'NICU': False}

                # Update family information
                if sample.udf['Dx NICU Spoed']:
                    families[family]['NICU'] = True
                    project_type = 'NICU_{0}'.format(sample.udf['Dx Familienummer'])
                    families[family]['project_type'] = project_type

                elif 'elidS30409818' in sample.udf['Dx Protocolomschrijving'] and not families[family]['NICU']:
                    project_type = 'CREv2'
                    families[family]['project_type'] = project_type

                # Add sample to family
                families[family]['samples'].append(sample)
            else:
                # TODO: Handle non dx samples
                continue

    # Get all project types and count samples
    project_types = {}
    for family in families.values():
        if family['project_type'] in project_types:
            project_types[family['project_type']]['sample_count'] += len(family['samples'])
        else:
            project_types[family['project_type']] = {'sample_count': len(family['samples']), 'projects': []}

    # Define projects per project_type
    for project_type in project_types:
        project_types[project_type]['index'] = 0
        for i in range(0, project_types[project_type]['sample_count']/9+1):
            project_types[project_type]['projects'].append('{0}_{1}'.format(project_type, i+1))

    # Set sample projects
    sample_projects = {}
    for family in sorted(families.items(), key=lambda tup: (len(tup[1]["samples"])), reverse=True):
        family_project_type = project_types[family[1]['project_type']]
        family_project = family_project_type['projects'][family_project_type['index']]

        for sample in family[1]['samples']:
            sample_projects[get_sequence_name(sample)] = family_project

        if family_project_type['index'] == len(family_project_type['projects']) - 1:
            family_project_type['index'] = 0
        else:
            family_project_type['index'] += 1

    # Edit clarity samplesheet
    header = ''  # empty until [data] section
    samplesheet_artifact = Artifact(lims, id=artifact_id)
    file_id = samplesheet_artifact.files[0].id

    for line in lims.get_file_contents(id=file_id).rstrip().split('\n'):
        if line.startswith('Sample_ID'):  # Samples header line
            header = line.rstrip().split(',')
            output_file.write('{line}\n'.format(line=line))

        elif header:  # Samples header seen, so continue with samples.
            data = line.rstrip().split(',')
            sample_id_index = header.index('Sample_ID')
            sample_name_index = header.index('Sample_Name')
            sample_project_index = header.index('Sample_Project')

            # Set Sample_Project
            try:
                data[sample_project_index] = sample_projects[data[sample_name_index]]
            except KeyError:
                pass

            # Overwrite Sample_ID with Sample_name to get correct conversion output folder structure
            data[sample_id_index] = data[sample_name_index]

            output_file.write('{line}\n'.format(line=','.join(data)))
        else:  # Leave other lines untouched.
            output_file.write('{line}\n'.format(line=line))
