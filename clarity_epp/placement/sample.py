"""Sample placement functions."""
from itertools import chain

from genologics.entities import Process

import config


def find_mip_sample(lims, process_id):
    """Find mip samples from same person"""
    process = Process(lims, id=process_id)

    # Get process samples, asumes one sample per artifact
    process_samples = [artifact.samples[0] for artifact in process.all_inputs(unique=True)]
    for sample in  process_samples:
        related_mip_samples = lims.get_samples(udf={
            'Dx Persoons ID': sample.udf['Dx Persoons ID'],
            'Dx Stoftest code': config.stoftestcode_mip
        })
        print(sample, related_mip_samples)


def find_wes_sample(lims, process_id):
    """Find mip samples from same person"""
    process = Process(lims, id=process_id)
    print(process)