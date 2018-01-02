"""Workflow export functions."""

from genologics.entities import Process, SampleHistory, Processtype


def helix(lims, process_id, output_file):
    """Export workflow information in helix table format."""
    output_file.write("<meet_id>\tOnderzoeksnummer\tmeetw_zui\tmeetw_zui_herh\tmeetw_libprep\tmeetw_libprep_herh\tmeetw_enrich\tmeetw_enrich_herh\tmeetw_seq\tmeetw_seq_herh\n")
    process = Process(lims, id=process_id)

    for sample in process.all_inputs()[0].samples:
        output_file.write(
            "{meet_id}\t{onderzoeksnummer}\tmeetw_zui\tmeetw_zui_herh\tmeetw_libprep\tmeetw_libprep_herh\tmeetw_enrich\tmeetw_enrich_herh\tmeetw_seq\tmeetw_seq_herh\n".format(
                meet_id=sample.udf['Dx Meet ID'],
                onderzoeksnummer=sample.udf['Dx Onderzoeknummer'],
            )
        )

        # sample_hist = SampleHistory(sample_name=sample.name, lims=lims)
        # process_type = Processtype(lims, id='354')
        # print lims.get_artifacts(sample_name=sample.name, process_type=process_type.name)
