"""Tapestation QC epp functions."""

from genologics.entities import Process


def set_qc_flag(lims, process_id):
    """Set tapestation qc flags based on Dx Fragmentlengte (bp) udf and criterea set by users."""
    process = Process(lims, id=process_id)

    min_size = process.udf['Minimale fragmentlengte (bp)']
    max_size = process.udf['Maximale fragmentlengte (bp)']

    for artifact in process.result_files():
        size = artifact.udf['Dx Fragmentlengte (bp)']
        if size >= min_size and size <= max_size:
            artifact.qc_flag = 'PASSED'
        else:
            artifact.qc_flag = 'FAILED'
        artifact.put()
