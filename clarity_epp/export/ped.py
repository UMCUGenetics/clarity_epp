"""Export ped functions."""
from genologics.entities import Process

from .. import get_sequence_name, get_sample_artifacts_from_pool


def create_file(lims, process_id, output_file):
    """Create ped file."""
    process = Process(lims, id=process_id)

    # Get output container assume one flowcell per sequencing run
    output_container = process.output_containers()[0]

    # Get unique sample artifacts in run
    # TODO: This is a copy of the code from merge.py. It should be refactored to a common function.
    sample_artifacts = []
    for lane_artifact in output_container.get_placements().values():
        for sample_artifact in get_sample_artifacts_from_pool(lims, lane_artifact):
            if sample_artifact not in sample_artifacts:
                sample_artifacts.append(sample_artifact)

    ped_families = {}

    for sample_artifact in sample_artifacts:
        sample = sample_artifact.samples[0]  # Asume all samples metadata is identical.

        if 'Dx Familienummer' in sample.udf and sample.udf['Dx Onderzoeksreden'] != 'Research':
            family = sample.udf['Dx Familienummer']
            sample_name = get_sequence_name(sample_artifact)
            ped_sample = {'name': sample_name}

            if family not in ped_families:
                ped_families[family] = {
                    'father': {},
                    'mother': {},
                    'children': [],
                    'unrelated': []
                }

            if sample.udf['Dx Geslacht'].lower() == 'man':
                ped_sample['sex'] = 1
            elif sample.udf['Dx Geslacht'].lower() == 'vrouw':
                ped_sample['sex'] = 2
            elif sample.udf['Dx Geslacht'].lower() == 'onbekend':
                ped_sample['sex'] = 0

            # Determine affection
            ped_sample['affection'] = 0  # unknown
            if 'Bevestiging diagnose' in sample.udf['Dx Onderzoeksreden']:
                ped_sample['affection'] = 2  # affected
            elif 'Informativiteitstest' in sample.udf['Dx Onderzoeksreden']:
                ped_sample['affection'] = 1  # unaffected
            elif 'Partner onderzoek' in sample.udf['Dx Onderzoeksreden']:
                ped_sample['affection'] = 1  # unaffected

            # Determine family relationships
            if (
                'Dx Gerelateerde onderzoeken' not in sample.udf
                and 'Dx gerelateerd aan oz' not in sample.udf
            ):
                ped_families[family]['unrelated'].append(ped_sample)
            elif sample.udf['Dx Familie status'] == 'Ouder' and ped_sample['sex'] == 1:
                ped_families[family]['father'] = ped_sample
            elif sample.udf['Dx Familie status'] == 'Ouder' and ped_sample['sex'] == 2:
                ped_families[family]['mother'] = ped_sample
            else:
                ped_families[family]['children'].append(ped_sample)

    for family in ped_families:
        ped_family = ped_families[family]
        paternal_sample_name = '0'
        maternal_sample_name = '0'

        if ped_family['father']:
            paternal_sample_name = ped_family['father']['name']
            output_file.write('{family}\t{name}\t{paternal_sample}\t{maternal_sample}\t{sex}\t{affection}\n'.format(
                family=family,
                name=ped_family['father']['name'],
                paternal_sample='0',
                maternal_sample='0',
                sex=ped_family['father']['sex'],
                affection=ped_family['father']['affection'],
            ))
        if ped_family['mother']:
            maternal_sample_name = ped_family['mother']['name']
            output_file.write('{family}\t{name}\t{paternal_sample}\t{maternal_sample}\t{sex}\t{affection}\n'.format(
                family=family,
                name=ped_family['mother']['name'],
                paternal_sample='0',
                maternal_sample='0',
                sex=ped_family['mother']['sex'],
                affection=ped_family['mother']['affection'],
            ))
        for child_sample in ped_family['children']:
            output_file.write('{family}\t{name}\t{paternal_sample}\t{maternal_sample}\t{sex}\t{affection}\n'.format(
                family=family,
                name=child_sample['name'],
                paternal_sample=paternal_sample_name,
                maternal_sample=maternal_sample_name,
                sex=child_sample['sex'],
                affection=child_sample['affection'],
            ))
        for unrelated_sample in ped_family['unrelated']:
            output_file.write('{family}\t{name}\t{paternal_sample}\t{maternal_sample}\t{sex}\t{affection}\n'.format(
                family=family,
                name=unrelated_sample['name'],
                paternal_sample='0',
                maternal_sample='0',
                sex=unrelated_sample['sex'],
                affection=unrelated_sample['affection'],
            ))
