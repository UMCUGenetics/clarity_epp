"""Export ped functions."""
from genologics.entities import Process

from .. import get_sequence_name


def create_file(lims, process_id, output_file):
    """Create ped file."""
    process = Process(lims, id=process_id)
    samples = process.analytes()[0][0].samples

    ped_families = {}

    for sample in samples:
        family = sample.udf['Dx Unummer']
        sample_name = get_sequence_name(sample)
        ped_sample = {'name': sample_name}

        if family not in ped_families:
            ped_families[family] = {
                'father': {},
                'mother': {},
                'children': []
            }

        if sample.udf['Dx Geslacht'].lower() == 'man':
            ped_sample['sex'] = 1
        elif sample.udf['Dx Geslacht'].lower() == 'vrouw':
            ped_sample['sex'] = 2
        elif sample.udf['Dx Geslacht'].lower() == 'onbekend':
            ped_sample['sex'] = 0

        # Determine affection
        ped_sample['affection'] = 0
        if sample.udf['Dx Onderzoeksreden'] == 'Bevestiging diagnose':
            ped_sample['affection'] = 2
        elif sample.udf['Dx Onderzoeksreden'] == 'Informativiteitstest':
            ped_sample['affection'] = 1

        # Determine family relationships
        if sample.udf['Dx Familie status'] == 'Ouder' and ped_sample['sex'] == 1:
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
                paternal_sample='',
                maternal_sample='',
                sex=ped_family['father']['sex'],
                affection=ped_family['father']['affection'],
            ))
        if ped_family['mother']:
            maternal_sample_name = ped_family['mother']['name']
            output_file.write('{family}\t{name}\t{paternal_sample}\t{maternal_sample}\t{sex}\t{affection}\n'.format(
                family=family,
                name=ped_family['mother']['name'],
                paternal_sample='',
                maternal_sample='',
                sex=ped_family['mother']['sex'],
                affection=ped_family['mother']['affection'],
            ))
        for child in ped_family['children']:
            child_sample = ped_family['children'][child]
            output_file.write('{family}\t{name}\t{paternal_sample}\t{maternal_sample}\t{sex}\t{affection}\n'.format(
                family=family,
                name=child_sample['name'],
                paternal_sample=paternal_sample_name,
                maternal_sample=maternal_sample_name,
                sex=child_sample['sex'],
                affection=child_sample['affection'],
            ))
