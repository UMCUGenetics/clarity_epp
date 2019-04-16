"""Export merge file functions."""
from genologics.entities import Process

from .. import get_sequence_name


def create_file(lims, process_id, output_file):
    """Create mege file."""
    process = Process(lims, id=process_id)
    samples = process.analytes()[0][0].samples

    output_file.write('Sample\tDx Mergen sample 1\tDx Mergen sample 2\n')

    for sample in samples:
        sample_merge = []
        if 'Dx Mergen' in sample.udf and sample.udf['Dx Mergen']:
            if 'Dx Mergen sample 1' in sample.udf:
                sample_merge.append(sample.udf['Dx Mergen sample 1'])
            else:
                sample_merge.append('')

            if 'Dx Mergen sample 2' in sample.udf:
                sample_merge.append(sample.udf['Dx Mergen sample 2'])
            else:
                sample_merge.append('')

            output_file.write('{sample}\t{merge}\n'.format(
                sample=get_sequence_name(sample),
                merge='\t'.join(sample_merge)
            ))
