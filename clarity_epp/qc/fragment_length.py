"""Fragment length QC epp functions."""

from genologics.entities import Process
import config


def set_qc_flag(lims, process_id):
    """Set qc flags based on Dx Fragmentlengte (bp) udf and criterea set by users."""
    process = Process(lims, id=process_id)

    min_size = process.udf['Minimale fragmentlengte (bp)']
    max_size = process.udf['Maximale fragmentlengte (bp)']

    for artifact in process.all_outputs():
        try:
            size = artifact.udf['Dx Fragmentlengte (bp)']
            if size >= min_size and size <= max_size:
                artifact.qc_flag = 'PASSED'
            else:
                artifact.qc_flag = 'FAILED'
        except KeyError:
            artifact.qc_flag = 'FAILED'
        finally:
            artifact.put()


def set_fragment_length_udf(lims, process_id):
    """Checks for empty fragment length udf and if so and WGS, fills it with 'fragment_length_wgs' from config."""
    process = Process(lims, id=process_id)

    for artifact in process.all_inputs():
        if 'Dx Fragmentlengte (bp)' not in artifact.udf or artifact.udf['Dx Fragmentlengte (bp)'] == "":
            if 'Dx QC check WGS prep' in artifact.workflow_stages_and_statuses[0][2]:
                artifact.udf['Dx Fragmentlengte (bp)'] = config.fragment_length_wgs
                artifact.put()
