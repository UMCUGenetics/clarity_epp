"""Illumina export functions."""
import operator
import re
import csv

from genologics.entities import Process, Artifact

from .. import get_sequence_name, get_sample_artifacts_from_pool
import clarity_epp.export.utils
import config


def get_project(projects, urgent=False):
    """Get a project name for sample."""
    if urgent:  # Sort projects for urgent samples on name
        projects_sorted = sorted(projects.items(), key=operator.itemgetter(0))
        for project in projects_sorted:
            if project[1] < 9:
                return project[0]  # return first project with < 9 samples

    # Sort projects on number of samples, if not urgent or no projects left with <9 samples
    projects_sorted = sorted(projects.items(), key=operator.itemgetter(1))
    return projects_sorted[0][0]  # return project with least amount of samples.


def get_override_cycles(read_len, umi_len, index_len, max_index_len, index_2_orientation):
    """Get override cycles per sample."""

    # Read cycles, Trim last base from read cycles
    read_1_cycle = f'Y{read_len[0]-1}N1'
    read_2_cycle = f'Y{read_len[1]-1}N1'

    # Adjust read cycles if umi present
    if umi_len[0]:
        read_1_cycle = f'U{umi_len[0]}Y{read_len[0]-1-umi_len[0]}N1'
    if umi_len[1]:
        read_2_cycle = f'U{umi_len[1]}Y{read_len[1]-1-umi_len[1]}N1'

    # Index cycles
    index_1_cycle = f'I{index_len[0]}'
    index_2_cycle = f'I{index_len[1]}'

    # Adjust if index length is shorter than max index length
    if index_len[0] < max_index_len[0]:
        n_bases = max_index_len[0] - index_len[0]
        index_1_cycle = f'I{index_len[0]}N{n_bases}'

    if index_len[1] < max_index_len[1]:
        n_bases = max_index_len[1] - index_len[1]
        if index_2_orientation == 'RC':
            index_2_cycle = f'I{index_len[1]}N{n_bases}'
        else:  # index_2_orientation == 'F
            index_2_cycle = f'N{n_bases}I{index_len[1]}'

    override_cycles = ';'.join([
        read_1_cycle,  # read 1
        index_1_cycle,  # index 1
        index_2_cycle,  # index 2
        read_2_cycle,  # read 2
    ])

    return override_cycles


def get_samplesheet_samples(sample_artifacts, process, index_2_orientation):
    families = {}
    samplesheet_samples = {}

    for sample_artifact in sample_artifacts:
        # Find sample artifact index, expected pattern = "<index name> (index1-index2)"
        sample_index = re.search(r".*\(([ACTGN]+)-([ACTGN]+)\)$", sample_artifact.reagent_labels[0])
        sample_sequence_name = get_sequence_name(sample_artifact)

        for sample in sample_artifact.samples:
            # Dx production sample
            if (
                'Dx Familienummer' in list(sample.udf) and
                'Dx NICU Spoed' in list(sample.udf) and
                'Dx Protocolomschrijving' in list(sample.udf) and
                'Dx Stoftest code' in list(sample.udf)
            ):
                # Skip Mengfractie samples
                if sample.udf['Dx Stoftest code'] == config.stoftestcode_wes_duplo:
                    continue

                # Get sample conversion_settings
                sample_conversion_setting = config.conversion_settings['default']
                newest_protocol = sample.udf['Dx Protocolomschrijving'].split(';')[0]
                for protocol_code in config.conversion_settings:
                    if protocol_code in newest_protocol:
                        sample_conversion_setting = config.conversion_settings[protocol_code]
                        break

                # Get sample override cycles
                sample_override_cycles = get_override_cycles(
                    read_len=[process.udf['Read 1 Cycles'], process.udf['Read 2 Cycles']],
                    umi_len=sample_conversion_setting['umi_len'],
                    index_len=[len(sample_index.group(1)), len(sample_index.group(2))],
                    max_index_len=[process.udf['Index Read 1'], process.udf['Index Read 2']],
                    index_2_orientation=index_2_orientation
                )

                # Set family and create if not exist
                family = sample.udf['Dx Familienummer']
                if family not in families:
                    families[family] = {
                        'samples': [],
                        'NICU': False,
                        'project_type': sample_conversion_setting['project'],
                        'split_project_type': sample_conversion_setting['split_project'],
                        'urgent': False,
                        'deviating': False  # merge, deep sequencing (5x), etc samples
                    }

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
                        families[family]['project_type'] = 'NICU_{0}'.format(sample.udf['Dx Familienummer'])
                        families[family]['split_project_type'] = False

                    # Set urgent status
                    if 'Dx Spoed' in list(sample.udf) and sample.udf['Dx Spoed']:
                        families[family]['urgent'] = True

                    # Set deviating status, remove urgent status if deviating
                    if (
                        ('Dx Mergen' in list(sample.udf) and sample.udf['Dx Mergen']) or
                        ('Dx Exoomequivalent' in list(sample.udf) and sample.udf['Dx Exoomequivalent'] > 1)
                    ):
                        families[family]['deviating'] = True
                        families[family]['urgent'] = False

            else:  # Other samples
                # Use project name as family name and Remove 'dx' (ignore case) and strip leading space or _
                family = re.sub('^dx[ _]*', '', sample.project.name, flags=re.IGNORECASE)
                if family not in families:
                    families[family] = {
                        'samples': [],
                        'NICU': False,
                        'project_type': family,
                        'split_project_type': False,
                        'urgent': False,
                        'deviating': False
                    }

                # Setup override cycles
                if 'Dx Override Cycles' in list(sample.udf) and sample.udf['Dx Override Cycles']:
                    sample_override_cycles = sample.udf['Dx Override Cycles']
                else:
                    sample_override_cycles = get_override_cycles(
                        read_len=[process.udf['Read 1 Cycles'], process.udf['Read 2 Cycles']],
                        umi_len=config.conversion_settings['default']['umi_len'],
                        index_len=[len(sample_index.group(1)), len(sample_index.group(2))],
                        max_index_len=[process.udf['Index Read 1'], process.udf['Index Read 2']],
                        index_2_orientation=index_2_orientation
                    )

            # Add sample to samplesheet_samples
            samplesheet_samples[sample_sequence_name] = {
                'index_1': sample_index.group(1),
                'index_2': sample_index.group(2),
                'override_cycles': sample_override_cycles,
            }
            if index_2_orientation == 'RC':  # Reverse complement index 2
                samplesheet_samples[sample_sequence_name]['index_2'] = clarity_epp.export.utils.reverse_complement(
                    samplesheet_samples[sample_sequence_name]['index_2']
                )

            # Add sample to family
            if sample_sequence_name not in families[family]['samples']:
                families[family]['samples'].append(sample_sequence_name)

    # Get all project types and count samples
    project_types = {}
    for family in families.values():
        if family['project_type'] in project_types:
            project_types[family['project_type']]['sample_count'] += len(family['samples'])
        else:
            project_types[family['project_type']] = {
                'sample_count': len(family['samples']),
                'projects': {},
                'split_project_type': family['split_project_type']
            }

    # Define projects per project_type
    for project_type in project_types:
        project_types[project_type]['index'] = 0
        if project_types[project_type]['split_project_type']:
            for i in range(0, int(project_types[project_type]['sample_count']/9+1)):
                project_types[project_type]['projects']['{0}_{1}'.format(project_type, i+1)] = 0
        else:
            project_types[project_type]['projects'][project_type] = 0

    # Set sample projects
    # Urgent families / samples, skip deviating
    for family in [family for family in families.values() if family['urgent'] and not family['deviating']]:
        family_project = get_project(project_types[family['project_type']]['projects'], urgent=True)
        for sample_sequence_name in family['samples']:
            samplesheet_samples[sample_sequence_name]['project'] = family_project
            project_types[family['project_type']]['projects'][family_project] += 1

    # Deviating families / samples
    for family in [family for family in families.values() if family['deviating']]:
        family_project = get_project(project_types[family['project_type']]['projects'])
        for sample_sequence_name in family['samples']:
            samplesheet_samples[sample_sequence_name]['project'] = family_project
            project_types[family['project_type']]['projects'][family_project] += 1

    # Non urgent and non deviating families / samples
    normal_families = [family for family in families.values() if not family['urgent'] and not family['deviating']]
    for family in sorted(normal_families, key=lambda fam: (len(fam['samples'])), reverse=True):
        family_project = get_project(project_types[family['project_type']]['projects'])
        for sample_sequence_name in family['samples']:
            samplesheet_samples[sample_sequence_name]['project'] = family_project
            project_types[family['project_type']]['projects'][family_project] += 1

    return samplesheet_samples


def create_samplesheet(lims, process_id, output_file):
    """Create illumina samplesheet v2."""
    process = Process(lims, id=process_id)
    index_2_orientation = config.index_2_orientation[process.type.name]

    # Get samples samples per lane
    samplesheet_samples = []
    for lane in process.analytes()[0]:
        sample_artifacts = get_sample_artifacts_from_pool(lims, process.analytes()[0][0])
        samplesheet_samples.append(get_samplesheet_samples(sample_artifacts, process, index_2_orientation))

    # Create SampleSheet
    sample_sheet = []

    # Header
    sample_sheet.append('[Header]')
    sample_sheet.append('FileFormatVersion,2')

    # Reads
    sample_sheet.append('[Reads]')
    sample_sheet.append('Read1Cycles,{0}'.format(process.udf['Read 1 Cycles']))
    sample_sheet.append('Read2Cycles,{0}'.format(process.udf['Read 2 Cycles']))

    # BCLConvert_Settings
    sample_sheet.append('[BCLConvert_Settings]')
    sample_sheet.append('AdapterRead1,{0}'.format(process.udf['Adapter']))
    sample_sheet.append('AdapterRead2,{0}'.format(process.udf['Adapter Read 2']))
    sample_sheet.append('FindAdaptersWithIndels,true')

    # BCLConvert_Data
    sample_sheet.append('[BCLConvert_Data]')
    if len(samplesheet_samples) == 1:  # All samples on all lanes
        lane = 0
        sample_sheet.append('Sample_ID,index,index2,OverrideCycles,Sample_Project')
        for sample in samplesheet_samples[lane]:
            sample_sheet.append(
                '{sample_name},{index_1},{index_2},{override_cycles},{project}'.format(
                    sample_name=sample,
                    index_1=samplesheet_samples[lane][sample]['index_1'],
                    index_2=samplesheet_samples[lane][sample]['index_2'],
                    override_cycles=samplesheet_samples[lane][sample]['override_cycles'],
                    project=samplesheet_samples[lane][sample]['project']
                )
            )
    else:  # Samples divided over lanes
        sample_sheet.append('Lane,Sample_ID,index,index2,OverrideCycles,Sample_Project')
        for lane, lane_samples in enumerate(samplesheet_samples):
            for sample in lane_samples:
                sample_sheet.append(
                    '{lane},{sample_name},{index_1},{index_2},{override_cycles},{project}'.format(
                        lane=lane+1,
                        sample_name=sample,
                        index_1=samplesheet_samples[lane][sample]['index_1'],
                        index_2=samplesheet_samples[lane][sample]['index_2'],
                        override_cycles=samplesheet_samples[lane][sample]['override_cycles'],
                        project=samplesheet_samples[lane][sample]['project']
                    )
                )

    output_file.write('\n'.join(sample_sheet))


def update_samplesheet(lims, process_id, artifact_id, output_file, conversion_tool):
    """Update illumina samplesheet."""
    process = Process(lims, id=process_id)
    trim_last_base = True  # Used to set Read1EndWithCycle

    def get_project(projects, urgent=False):
        """Inner function to get a project name for samples."""
        if urgent:  # Sort projects for urgent samples on name
            projects_sorted = sorted(projects.items(), key=operator.itemgetter(0))
            for project in projects_sorted:
                if project[1] < 9:
                    return project[0]  # return first project with < 9 samples

        # Sort projects on number of samples, if not urgent or no projects left with <9 samples
        projects_sorted = sorted(projects.items(), key=operator.itemgetter(1))
        return projects_sorted[0][0]  # return project with least amount of samples.

    # Parse families
    families = {}
    sample_artifacts = get_sample_artifacts_from_pool(lims, process.analytes()[0][0])

    for sample_artifact in sample_artifacts:
        for sample in sample_artifact.samples:
            if (
                'Dx Familienummer' in list(sample.udf) and
                'Dx NICU Spoed' in list(sample.udf) and
                'Dx Protocolomschrijving' in list(sample.udf)
            ):
                # Dx production sample
                family = sample.udf['Dx Familienummer']

                # Create family if not exist
                if family not in families:
                    families[family] = {
                        'samples': [],
                        'NICU': False,
                        'project_type': 'unknown_project',
                        'split_project_type': False,
                        'urgent': False,
                        'deviating': False  # merge, deep sequencing (5x), etc samples
                    }

                # Update family information
                if sample.udf['Dx Onderzoeksreden'] == 'Research':  # Dx research sample
                    for onderzoeksindicatie in config.research_onderzoeksindicatie_project:
                        if sample.udf['Dx Onderzoeksindicatie'] == onderzoeksindicatie:
                            project_type = config.research_onderzoeksindicatie_project[onderzoeksindicatie]
                            families[family]['project_type'] = project_type
                            families[family]['split_project_type'] = False
                            break

                else:  # Dx clinic sample
                    newest_protocol = sample.udf['Dx Protocolomschrijving'].split(';')[0]
                    if 'SNP fingerprint MIP' in newest_protocol and not families[family]['NICU']:
                        project_type = 'Fingerprint'
                        families[family]['project_type'] = project_type
                        families[family]['split_project_type'] = False
                        trim_last_base = False
                    elif 'PID09.V7_smMIP' in newest_protocol and not families[family]['NICU']:
                        project_type = 'ERARE'
                        families[family]['project_type'] = project_type
                        families[family]['split_project_type'] = False
                        trim_last_base = False
                    elif sample.udf['Dx NICU Spoed']:
                        families[family]['NICU'] = True
                        project_type = 'NICU_{0}'.format(sample.udf['Dx Familienummer'])
                        families[family]['project_type'] = project_type
                        families[family]['split_project_type'] = False
                    elif 'elidS30409818' in newest_protocol and not families[family]['NICU']:
                        project_type = 'CREv2'
                        families[family]['project_type'] = project_type
                        families[family]['split_project_type'] = True
                    elif 'elidS31285117' in newest_protocol and not families[family]['NICU']:
                        project_type = 'SSv7'
                        families[family]['project_type'] = project_type
                        families[family]['split_project_type'] = True
                    elif 'elidS34226467' in newest_protocol and not families[family]['NICU']:
                        project_type = 'CREv4'
                        families[family]['project_type'] = project_type
                        families[family]['split_project_type'] = True

                    # Set urgent status
                    if 'Dx Spoed' in list(sample.udf) and sample.udf['Dx Spoed']:
                        families[family]['urgent'] = True

                    # Set deviating status, remove urgent status if deviating
                    if (
                        ('Dx Mergen' in list(sample.udf) and sample.udf['Dx Mergen']) or
                        ('Dx Exoomequivalent' in list(sample.udf) and sample.udf['Dx Exoomequivalent'] > 1)
                    ):
                        families[family]['deviating'] = True
                        families[family]['urgent'] = False

            else:  # Other samples
                if 'GIAB' in sample.name.upper() and not sample.project:  # GIAB control samples
                    family = 'GIAB'
                else:
                    family = sample.project.name
                    # Remove 'dx' (ignore case) and strip leading space or _
                    family = re.sub('^dx[ _]*', '', family, flags=re.IGNORECASE)
                if family not in families:
                    families[family] = {
                        'samples': [],
                        'NICU': False,
                        'project_type': family,
                        'split_project_type': False,
                        'urgent': False,
                        'deviating': False
                    }

            # Add sample_artifact to family
            if sample_artifact not in families[family]['samples']:
                families[family]['samples'].append(sample_artifact)

    # Get all project types and count samples
    project_types = {}
    for family in families.values():
        if family['project_type'] in project_types:
            project_types[family['project_type']]['sample_count'] += len(family['samples'])
        else:
            project_types[family['project_type']] = {
                'sample_count': len(family['samples']),
                'projects': {},
                'split_project_type': family['split_project_type']
            }

    # Define projects per project_type
    for project_type in project_types:
        project_types[project_type]['index'] = 0
        if project_types[project_type]['split_project_type']:
            for i in range(0, int(project_types[project_type]['sample_count']/9+1)):
                project_types[project_type]['projects']['{0}_{1}'.format(project_type, i+1)] = 0
        else:
            project_types[project_type]['projects'][project_type] = 0

    # Set sample projects
    sample_projects = {}
    sample_sequence_names = {}

    # Urgent families / samples, skip deviating
    for family in [family for family in families.values() if family['urgent'] and not family['deviating']]:
        family_project = get_project(project_types[family['project_type']]['projects'], urgent=True)
        for sample_artifact in family['samples']:
            sample_sequence_name = get_sequence_name(sample_artifact)
            for sample in sample_artifact.samples:
                sample_sequence_names[sample.name] = sample_sequence_name
            sample_projects[sample_sequence_name] = family_project
            project_types[family['project_type']]['projects'][family_project] += 1

    # Deviating families / samples
    for family in [family for family in families.values() if family['deviating']]:
        family_project = get_project(project_types[family['project_type']]['projects'])
        for sample_artifact in family['samples']:
            sample_sequence_name = get_sequence_name(sample_artifact)
            for sample in sample_artifact.samples:
                sample_sequence_names[sample.name] = sample_sequence_name
            sample_projects[sample_sequence_name] = family_project
            project_types[family['project_type']]['projects'][family_project] += 1

    # Non urgent and non deviating families / samples
    normal_families = [family for family in families.values() if not family['urgent'] and not family['deviating']]
    for family in sorted(normal_families, key=lambda fam: (len(fam['samples'])), reverse=True):
        family_project = get_project(project_types[family['project_type']]['projects'])
        for sample_artifact in family['samples']:
            sample_sequence_name = get_sequence_name(sample_artifact)
            for sample in sample_artifact.samples:
                sample_sequence_names[sample.name] = sample_sequence_name
            sample_projects[sample_sequence_name] = family_project
            project_types[family['project_type']]['projects'][family_project] += 1

    # Check sequencer type
    # NextSeq runs need to reverse complement 'index2' for dual barcodes and 'index' for single barcodes.
    if 'nextseq' in process.type.name.lower():
        nextseq_run = True
    else:
        nextseq_run = False

    # Edit clarity samplesheet
    sample_header = ''  # empty until [data] section
    settings_section = False
    samplesheet_artifact = Artifact(lims, id=artifact_id)
    file_id = samplesheet_artifact.files[0].id

    # Setup custom settings
    custom_settings = ''

    if conversion_tool == 'bcl2fastq' and trim_last_base:
        custom_settings = (
            'Read1EndWithCycle,{read_1_value}\n'
            'Read2EndWithCycle,{read_2_value}\n'
        ).format(
            read_1_value=process.udf['Read 1 Cycles']-1, read_2_value=process.udf['Read 2 Cycles']-1
        )

    elif conversion_tool == 'bclconvert':
        # Setup OverrideCycles
        if trim_last_base or process.udf['UMI - Trim']:
            override_cycles = [
                '',  # read 1
                'I{0}'.format(process.udf['Index Read 1']),  # index 1
                'I{0}'.format(process.udf['Index Read 2']),  # index 2
                '',  # read 2
            ]

            if trim_last_base and process.udf['UMI - Trim']:
                override_cycles[0] = 'U{umi}Y{read}N1'.format(
                    umi=process.udf['UMI - Read 1 Length'],
                    read=process.udf['Read 1 Cycles'] - process.udf['UMI - Read 1 Length'] - 1
                )
                override_cycles[3] = 'U{umi}Y{read}N1'.format(
                    umi=process.udf['UMI - Read 2 Length'],
                    read=process.udf['Read 2 Cycles'] - process.udf['UMI - Read 2 Length'] - 1
                )
                custom_settings = 'TrimUMI,1\n'

            elif trim_last_base:
                override_cycles[0] = 'Y{read}N1'.format(read=process.udf['Read 1 Cycles'] - 1)
                override_cycles[3] = 'Y{read}N1'.format(read=process.udf['Read 2 Cycles'] - 1)

            elif process.udf['UMI - Trim']:
                override_cycles[0] = 'U{umi}Y{read}'.format(
                    umi=process.udf['UMI - Read 1 Length'],
                    read=process.udf['Read 1 Cycles'] - process.udf['UMI - Read 1 Length']
                )
                override_cycles[3] = 'U{umi}Y{read}'.format(
                    umi=process.udf['UMI - Read 2 Length'],
                    read=process.udf['Read 2 Cycles'] - process.udf['UMI - Read 2 Length']
                )
                custom_settings = 'TrimUMI,1\n'

            custom_settings = '{settings}OverrideCycles,{override_cycles}\n'.format(
                settings=custom_settings,
                override_cycles=';'.join(override_cycles)
            )

    for data in csv.reader(
        lims.get_file_contents(id=file_id).rstrip().split('\n'),
        quotechar='"', delimiter=',', quoting=csv.QUOTE_ALL, skipinitialspace=True
    ):
        if data[0] == '[Settings]' and custom_settings:
            output_file.write('{line}\n'.format(line=','.join(data)))
            output_file.write(custom_settings)
            settings_section = True

        elif data[0] == '[Data]' and custom_settings and not settings_section:
            output_file.write('[Settings]\n')
            output_file.write(custom_settings)
            output_file.write('{line}\n'.format(line=','.join(data)))

        elif data[0] == 'Sample_ID':  # Samples header line
            sample_header = data
            sample_id_index = sample_header.index('Sample_ID')
            sample_name_index = sample_header.index('Sample_Name')
            sample_project_index = sample_header.index('Sample_Project')

            if 'index2' in sample_header:
                index_index = sample_header.index('index2')
            else:
                index_index = sample_header.index('index')

            output_file.write('{line}\n'.format(line=','.join(data)))

        elif sample_header:  # Samples header seen, so continue with samples.
            sample_name = data[sample_name_index].split(',')[0]
            if sample_name in sample_sequence_names:
                data[sample_name_index] = sample_sequence_names[sample_name]

            # Set Sample_Project
            if data[sample_name_index] in sample_projects:
                data[sample_project_index] = sample_projects[data[sample_name_index]]

            # Overwrite Sample_ID with Sample_name to get correct conversion output folder structure
            data[sample_id_index] = data[sample_name_index]

            # Reverse complement index for NextSeq runs
            if nextseq_run:
                data[index_index] = clarity_epp.export.utils.reverse_complement(data[index_index])

            output_file.write('{line}\n'.format(line=','.join(data)))
        else:  # Leave other lines untouched.
            output_file.write('{line}\n'.format(line=','.join(data)))
