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
    """Checks for empty udf 'Dx Fragmentlengte (bp)' and fills it if
    udf 'Dx Protocolomschrijving' contains protocol description from config.fragment_length.

    Args:
        lims (object): Lims connection
        process_id (str): Process ID
    """
    process = Process(lims, id=process_id)

    for artifact in process.all_inputs():
        if 'Dx Fragmentlengte (bp)' not in artifact.udf or artifact.udf['Dx Fragmentlengte (bp)'] == "":
            for protocol in config.fragment_length:
                if protocol != 'default':
                    for sample in artifact.samples:
                        if 'Dx Protocolomschrijving' in sample.udf:
                            if protocol in sample.udf['Dx Protocolomschrijving']:
                                artifact.udf['Dx Fragmentlengte (bp)'] = config.fragment_length[protocol]
                                artifact.put()

            # No Dx Protocolomschijving or description not in config
            if 'Dx Fragmentlengte (bp)' not in artifact.udf or artifact.udf['Dx Fragmentlengte (bp)'] == "":
                artifact.udf['Dx Fragmentlengte (bp)'] = config.fragment_length['default']
                artifact.put()
