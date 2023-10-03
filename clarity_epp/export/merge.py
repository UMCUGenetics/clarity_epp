"""Export merge file functions."""
from genologics.entities import Process

from .. import get_sequence_name, get_sample_artifacts_from_pool


def create_file(lims, process_id, output_file):
    """Create mege file."""
    process = Process(lims, id=process_id)
    sample_artifacts = get_sample_artifacts_from_pool(lims, process.analytes()[0][0])

    output_file.write('Sample\tMerge 1 Sample\tMerge 1 Sequencing Run\tMerge 2 Sample\tMerge 2 Sequencing Run\n')

    # for sample in samples:
    for sample_artifact in sample_artifacts:
        for sample in sample_artifact.samples:  # Asumme one sample per sample_artifact contains merge information
            sample_merge = []
            if 'Dx Mergen' in sample.udf and sample.udf['Dx Mergen']:
                for udf in ['Dx Merge 1 Samplenaam', 'Dx Merge 1 Runnaam', 'Dx Merge 2 Samplenaam', 'Dx Merge 2 Runnaam']:
                    if udf in sample.udf:
                        sample_merge.append(sample.udf[udf])
                    else:
                        sample_merge.append('')

                output_file.write('{sample}\t{merge}\n'.format(
                    sample=get_sequence_name(sample_artifact),
                    merge='\t'.join(sample_merge)
                ))
