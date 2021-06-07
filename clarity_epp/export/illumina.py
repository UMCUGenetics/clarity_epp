"""Illumina export functions."""
import operator
import re

from genologics.entities import Process, Artifact

from .. import get_sequence_name
import clarity_epp.export.utils
import config


def update_samplesheet(lims, process_id, artifact_id, output_file):
    """Update illumina samplesheet."""
    process = Process(lims, id=process_id)

    def get_project(projects, urgent=False):
        """Inner function to get a project name for samples."""
        if urgent:  # Sort projects for urgent samples on name
            projects = sorted(projects.items(), key=operator.itemgetter(0))
            for project in projects:
                if project[1] < 9:
                    return project[0]  # return first project with < 9 samples
        else:  # Sort projects for other samples on number of samples
            projects = sorted(projects.items(), key=operator.itemgetter(1))
            return projects[0][0]  # return project with least amount of samples.

    # Parse families
    families = {}
    for artifact in process.all_inputs():
        for sample in artifact.samples:
            if 'Dx Familienummer' in list(sample.udf) and 'Dx NICU Spoed' in list(sample.udf) and 'Dx Protocolomschrijving' in list(sample.udf):
                # Dx production sample
                family = sample.udf['Dx Familienummer']

                # Create family if not exist
                if family not in families:
                    families[family] = {'samples': [], 'NICU': False, 'project_type': 'unknown_project', 'split_project_type': False, 'urgent': False, 'merge': False}

                # Update family information
                if sample.udf['Dx Onderzoeksreden'] == 'Research':  # Dx research sample
                    for onderzoeksindicatie in config.research_onderzoeksindicatie_project:
                        if sample.udf['Dx Onderzoeksindicatie'] == onderzoeksindicatie:
                            project_type = config.research_onderzoeksindicatie_project[onderzoeksindicatie]
                            families[family]['project_type'] = project_type
                            families[family]['split_project_type'] = False
                            break

                else:  # Dx clinic sample
                    if sample.udf['Dx NICU Spoed']:
                        families[family]['NICU'] = True
                        project_type = 'NICU_{0}'.format(sample.udf['Dx Familienummer'])
                        families[family]['project_type'] = project_type
                        families[family]['split_project_type'] = False
                    elif 'elidS30409818' in sample.udf['Dx Protocolomschrijving'] and not families[family]['NICU']:
                        project_type = 'CREv2'
                        families[family]['project_type'] = project_type
                        families[family]['split_project_type'] = True
                    elif 'SNP fingerprint MIP' in sample.udf['Dx Protocolomschrijving'] and not families[family]['NICU']:
                        project_type = 'Fingerprint'
                        families[family]['project_type'] = project_type
                        families[family]['split_project_type'] = False
                    elif 'PID09.V7_smMIP' in sample.udf['Dx Protocolomschrijving'] and not families[family]['NICU']:
                        project_type = 'ERARE'
                        families[family]['project_type'] = project_type
                        families[family]['split_project_type'] = False
                    
                    # Set urgent / merge status
                    if 'Dx Spoed' in list(sample.udf) and sample.udf['Dx Spoed']:
                        families[family]['urgent'] = True
                    if 'Dx Mergen' in list(sample.udf) and sample.udf['Dx Mergen']:
                        families[family]['merge'] = True
                        families[family]['urgent'] = False

            else:  # Other samples
                if 'GIAB' in sample.name.upper() and not sample.project:  # GIAB control samples
                    family = 'GIAB'
                else:
                    family = sample.project.name
                    family = re.sub('^dx[ _]*', '', family, flags=re.IGNORECASE)  # Remove 'dx' (ignore case) and strip leading space or _
                if family not in families:
                    families[family] = {'samples': [], 'NICU': False, 'project_type': family, 'split_project_type': False, 'urgent': False, 'merge': False}

            # Add sample to family
            families[family]['samples'].append(sample)

    # Get all project types and count samples
    project_types = {}
    for family in families.values():
        if family['project_type'] in project_types:
            project_types[family['project_type']]['sample_count'] += len(family['samples'])
        else:
            project_types[family['project_type']] = {'sample_count': len(family['samples']), 'projects': {}, 'split_project_type': family['split_project_type']}

    # Define projects per project_type
    for project_type in project_types:
        project_types[project_type]['index'] = 0
        if project_types[project_type]['split_project_type']:
            for i in range(0, project_types[project_type]['sample_count']/9+1):
                project_types[project_type]['projects']['{0}_{1}'.format(project_type, i+1)] = 0
        else:
            project_types[project_type]['projects'][project_type] = 0

    # Set sample projects
    sample_projects = {}

    # Urgent families / samples, skip merge
    for family in [family for family in families.values() if family['urgent'] and not family['merge']]:
        family_project = get_project(project_types[family['project_type']]['projects'], urgent=True)
        for sample in family['samples']:
            sample_projects[get_sequence_name(sample)] = family_project
            project_types[family['project_type']]['projects'][family_project] += 1
    
    # Merge families / samples
    for family in [family for family in families.values() if family['merge']]:
        family_project = get_project(project_types[family['project_type']]['projects'])
        for sample in family['samples']:
            sample_projects[get_sequence_name(sample)] = family_project
            project_types[family['project_type']]['projects'][family_project] += 1

    # Non urgent and non merge families / samples
    non_urgent_families = [family for family in families.values() if not family['urgent'] and not family['merge']]
    for family in sorted(non_urgent_families, key=lambda fam: (len(fam['samples'])), reverse=True):
        family_project = get_project(project_types[family['project_type']]['projects'])
        for sample in family['samples']:
            sample_projects[get_sequence_name(sample)] = family_project
            project_types[family['project_type']]['projects'][family_project] += 1

    # Check sequencer type -> NextSeq runs need to reverse complement 'index2' for dual barcodes and 'index' for single barcodes.
    if 'nextseq' in process.type.name.lower():
        nextseq_run = True
    else:
        nextseq_run = False

    # Edit clarity samplesheet
    sample_header = ''  # empty until [data] section
    settings_section = False
    samplesheet_artifact = Artifact(lims, id=artifact_id)
    file_id = samplesheet_artifact.files[0].id

    for line in lims.get_file_contents(id=file_id).rstrip().split('\n'):
        if line.startswith('[Settings]'):
            output_file.write('{line}\n'.format(line=line))
            output_file.write('Read1EndWithCycle,{value}\n'.format(value=process.udf['Read 1 Cycles']-1))
            output_file.write('Read2EndWithCycle,{value}\n'.format(value=process.udf['Read 2 Cycles']-1))
            settings_section = True

        elif line.startswith('[Data]') and not settings_section:
            output_file.write('[Settings]\n')
            output_file.write('Read1EndWithCycle,{value}\n'.format(value=process.udf['Read 1 Cycles']-1))
            output_file.write('Read2EndWithCycle,{value}\n'.format(value=process.udf['Read 2 Cycles']-1))
            output_file.write('{line}\n'.format(line=line))

        elif line.startswith('Sample_ID'):  # Samples header line
            sample_header = line.rstrip().split(',')
            sample_id_index = sample_header.index('Sample_ID')
            sample_name_index = sample_header.index('Sample_Name')
            sample_project_index = sample_header.index('Sample_Project')

            if 'index2' in sample_header:
                index_index = sample_header.index('index2')
            else:
                index_index = sample_header.index('index')

            output_file.write('{line}\n'.format(line=line))

        elif sample_header:  # Samples header seen, so continue with samples.
            data = line.rstrip().split(',')

            # Set Sample_Project
            try:
                data[sample_project_index] = sample_projects[data[sample_name_index]]
            except KeyError:
                pass

            # Overwrite Sample_ID with Sample_name to get correct conversion output folder structure
            data[sample_id_index] = data[sample_name_index]

            # Reverse complement index for NextSeq runs
            if nextseq_run:
                data[index_index] = clarity_epp.export.utils.reverse_complement(data[index_index])

            output_file.write('{line}\n'.format(line=','.join(data)))
        else:  # Leave other lines untouched.
            output_file.write('{line}\n'.format(line=line))
