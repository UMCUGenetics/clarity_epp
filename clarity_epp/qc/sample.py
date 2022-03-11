"""Sample placement functions."""
from genologics.entities import Process

import config
from .. import get_sequence_name


def set_mip_data_ready(lims, process_id):
    """Set mip data ready udf for wes samples from same person and test."""
    process = Process(lims, id=process_id)

    # Get process samples, asumes one sample per artifact
    process_samples = [artifact.samples[0] for artifact in process.all_inputs(unique=True)]
    for sample in process_samples:
        related_wes_samples = lims.get_samples(udf={
            'Dx Persoons ID': sample.udf['Dx Persoons ID'],
            'Dx Onderzoeknummer': sample.udf['Dx Onderzoeknummer'],
            'Dx Stoftest code': config.stoftestcode_wes
        })
        if related_wes_samples:
            for sample in related_wes_samples:
                # sample.udf['Dx mip available'] = True  # Do we need this?
                sample.udf['Dx mip'] = get_sequence_name(sample)
                sample.put()
        else:
            print(sample.name, "Can't find related WES sample.")