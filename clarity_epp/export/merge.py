"""Export merge file functions."""
from genologics.entities import Process

from .. import get_sequence_name


def create_file(lims, process_id, output_file):
    """Create mege file."""
    process = Process(lims, id=process_id)
    samples = process.analytes()[0][0].samples

    output_file.write('Sample\tMerge 1 Sequencing Run\tMerge 1 Sample\tMerge 2 Sequencing Run\tMerge 2 Sample\n')

    for sample in samples:
        sample_merge = []
        if 'Dx Mergen' in sample.udf and sample.udf['Dx Mergen']:
            for udf in ['Dx Merge 1 Runnaam', 'Dx Merge 1 Samplenaam', 'Dx Merge 2 Runnaam', 'Dx Merge 2 Samplenaam']:
                if udf in sample.udf:
                    sample_merge.append(sample.udf[udf])
                else:
                    sample_merge.append('')

            output_file.write('{sample}\t{merge}\n'.format(
                sample=get_sequence_name(sample),
                merge='\t'.join(sample_merge)
            ))
