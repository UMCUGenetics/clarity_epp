"""Illumina export functions."""
import operator
import re

from genologics.entities import Process

from .. import get_sequence_name, get_sample_artifacts_from_pool
from clarity_epp.export.utils import get_sample_sequence_index, reverse_complement
import config


def get_project(projects, urgent=False):
    """Get a project name from projects dict ({'project_name': sample_count, ...})
    If urgent is True, return the first project with < 9 samples, else return the project with the least amount of samples.
    """
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
    read_cycles = ['', '']
    index_cycles = ['', '']

    for idx in range(len(read_cycles)):
        if umi_len[idx]:  # read cycle with umi
            read_cycle = f'U{umi_len[idx]}Y{read_len[idx]-1-umi_len[idx]}N1'
        else:  # read cycle without umi
            read_cycle = f'Y{read_len[idx]-1}N1'
        read_cycles[idx] = read_cycle

    for idx in range(len(index_cycles)):
        if index_len[idx]:
            if index_len[idx] < max_index_len[idx]:
                n_bases = max_index_len[idx] - index_len[idx]
                if idx == 1 and index_2_orientation == 'F':  # Index 2 in forward orientation (NovaSeq X Plus)
                    index_cycle = f'N{n_bases}I{index_len[idx]}'
                else:
                    index_cycle = f'I{index_len[idx]}N{n_bases}'
            else:
                index_cycle = f'I{index_len[idx]}'
        else:  # empty index, single index library
            index_cycle = f'N{index_len[idx]}'
        index_cycles[idx] = index_cycle

    override_cycles = ';'.join([
        read_cycles[0],  # read 1
        index_cycles[0],  # index 1
        index_cycles[1],  # index 2
        read_cycles[1],  # read 2
    ])

    return override_cycles


def get_samplesheet_samples(sample_artifacts, process, index_2_orientation):
    families = {}
    samplesheet_samples = {}

    for sample_artifact in sample_artifacts:
        sample_sequence_name = get_sequence_name(sample_artifact)
        sample_index = get_sample_sequence_index(sample_artifact.reagent_labels[0])
        # Adjust empty second index for single index samples
        if len(sample_index) == 1:
            sample_index.append('')

        for sample in sample_artifact.samples:
            # Dx production sample
            if (
                'Dx Familienummer' in sample.udf and
                'Dx NICU Spoed' in sample.udf and
                'Dx Protocolomschrijving' in sample.udf and
                'Dx Stoftest code' in sample.udf
            ):
                # Skip Mengfractie samples
                if sample.udf['Dx Stoftest code'] == config.stoftestcode_wes_duplo:
                    continue

                # Get sample conversion_settings
                sample_conversion_setting = config.conversion_settings['default']
                newest_protocol = sample.udf['Dx Protocolomschrijving'].split(';')[0]
                for protocol_code in config.conversion_settings:
                    if protocol_code in newest_protocol:  # Look for protocol code (elid number) in newest protocol
                        sample_conversion_setting = config.conversion_settings[protocol_code]
                        break

                # Get sample override cycles
                sample_override_cycles = get_override_cycles(
                    read_len=[process.udf['Read 1 Cycles'], process.udf['Read 2 Cycles']],
                    umi_len=sample_conversion_setting['umi_len'],
                    index_len=[len(sample_index[0]), len(sample_index[1])],
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
                        index_len=[len(sample_index[0]), len(sample_index[1])],
                        max_index_len=[process.udf['Index Read 1'], process.udf['Index Read 2']],
                        index_2_orientation=index_2_orientation
                    )

            # Add sample to samplesheet_samples
            samplesheet_samples[sample_sequence_name] = {
                'index_1': sample_index[0],
                'index_2': sample_index[1],
                'override_cycles': sample_override_cycles,
            }
            if index_2_orientation == 'RC':  # Reverse complement index 2
                samplesheet_samples[sample_sequence_name]['index_2'] = reverse_complement(
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
    sample_sheet = [
        # Header
        "[Header]",
        "FileFormatVersion,2",
        f"RunName,{process.udf['Experiment Name']}",
        # Reads
        "[Reads]",
        f"Read1Cycles,{process.udf['Read 1 Cycles']}",
        f"Read2Cycles,{process.udf['Read 2 Cycles']}",
        f"Index1Cycles,{process.udf['Index Read 1']}",
        f"Index2Cycles,{process.udf['Index Read 2']}",
        # BCLConvert_Settings
        "[BCLConvert_Settings]",
        f"AdapterRead1,{process.udf['Adapter']}",
        f"AdapterRead2,{process.udf['Adapter Read 2']}",
        "FindAdaptersWithIndels,true",
        "BarcodeMismatchesIndex1,0",
        "BarcodeMismatchesIndex2,0",
        "[BCLConvert_Data]"
    ]

    # BCLConvert_Data
    # Set header for single or multiple lanes conversion
    bcl_convert_data_header = "Sample_ID,index,index2,OverrideCycles,Sample_Project"
    if len(samplesheet_samples) == 1:  # All samples on all lanes
        multiple_lanes = False
    else:
        multiple_lanes = True
        bcl_convert_data_header = f"Lane,{bcl_convert_data_header}"  # Add lane column to header if multiple lanes conversion
    sample_sheet.append(bcl_convert_data_header)

    # Add samples to SampleSheet
    for lane, lane_samples in enumerate(samplesheet_samples):
        for sample in lane_samples:
            bcl_convert_data_row = "{sample_name},{index_1},{index_2},{override_cycles},{project}".format(
                    sample_name=sample,
                    index_1=samplesheet_samples[lane][sample]['index_1'],
                    index_2=samplesheet_samples[lane][sample]['index_2'],
                    override_cycles=samplesheet_samples[lane][sample]['override_cycles'],
                    project=samplesheet_samples[lane][sample]['project']
                )
            if multiple_lanes:  # Add lane number to row if multiple lanes conversion
                bcl_convert_data_row = f"{lane+1},{bcl_convert_data_row}"
            sample_sheet.append(bcl_convert_data_row)

    # Write SampleSheet to file
    output_file.write('\n'.join(sample_sheet))
