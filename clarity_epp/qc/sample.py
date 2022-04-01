"""Sample placement functions."""
from genologics.entities import Process

import config
from .. import get_sequence_name


def set_mip_data_ready(lims, process_id):
    """Set mip data ready udf for wes samples from same person and test."""
    process = Process(lims, id=process_id)
    # Get process samples, asumes one sample per artifact and only use artifacts with workflow status == completed.
    process_samples = [
        action_artifact['artifact'].samples[0] for action_artifact in process.step.actions.get_next_actions()
        if action_artifact['action'] == 'complete'
    ]

    for sample in process_samples:
        # MIP sample
        if sample.udf['Dx Stoftest code'] == config.stoftestcode_mip:
            # Update MIP sample with data ready tag
            sample.udf['Dx data ready'] = True
            sample.put()

            # Find related WES sample and update related sample with sequence name of MIP sample
            related_wes_samples = lims.get_samples(udf={
                'Dx Persoons ID': sample.udf['Dx Persoons ID'],
                'Dx Onderzoeknummer': sample.udf['Dx Onderzoeknummer'],
                'Dx Stoftest code': config.stoftestcode_wes
            })
            if related_wes_samples:
                for related_wes_sample in related_wes_samples:
                    related_wes_sample.udf['Dx mip'] = get_sequence_name(sample)
                    related_wes_sample.put()

        # WES sample
        elif sample.udf['Dx Stoftest code'] == config.stoftestcode_wes:
            # Find related mip samples with data ready, update sample with sequence name of MIP sample
            related_mip_samples = lims.get_samples(udf={
                'Dx Persoons ID': sample.udf['Dx Persoons ID'],
                'Dx Onderzoeknummer': sample.udf['Dx Onderzoeknummer'],
                'Dx Stoftest code': config.stoftestcode_mip,
                'Dx data ready': True,
            })
            if related_mip_samples:
                for related_mip_sample in related_mip_samples:
                    sample.udf['Dx mip'] = get_sequence_name(related_mip_sample)
                    sample.put()
