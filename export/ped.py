"""Export ped functions."""
from genologics.entities import Process


def create_file(lims, process_id, output_file):
    """Create ped file."""
    process = Process(lims, id=process_id)
    samples = process.analytes()[0][0].samples

    for sample in samples:
        # Determine sex
        sample_sex = 'other'
        if sample.udf['Dx Geslacht'].lower() == 'man' or sample.udf['Dx Geslacht'].lower() == 'm':
            sample_sex = 1
        elif sample.udf['Dx Geslacht'].lower() == 'vrouw' or sample.udf['Dx Geslacht'].lower() == 'v':
            sample_sex = 2

        # Determine parents

        # Determine affection
        affection = 0

        output_file.write('{family}\t{sample}\t{paternal_sample}\t{maternal_sample}\t{sex}\t{affection}\n'.format(
            family=sample.udf['Dx Unummer'],
            sample=sample.name,  # change to ped/sequencing name
            paternal_sample='',
            maternal_sample='',
            sex=sample_sex,
            affection=affection,
        ))
