"""Fragment length QC epp functions."""

from genologics.entities import Process


def set_qc_flag(lims, process_id):
    """Set qc flags based on Dx Fragmentlengte (bp) udf and criterea set by users."""
    process = Process(lims, id=process_id)

    min_size = process.udf['Minimale fragmentlengte (bp)']
    max_size = process.udf['Maximale fragmentlengte (bp)']

    for artifact in process.all_outputs():
        print artifact, artifact.name, artifact.files
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
