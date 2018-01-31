"""Workflow export functions."""

from genologics.entities import Process, SampleHistory


def determin_meetw(meetw_processes, sample_processes):
    """Determine meetw and meetw_herh based on list of processes."""
    meetw = 0
    meetw_herh = 0

    for process in meetw_processes:
        if process in sample_processes:
            if sample_processes[process] == 1:
                meetw = 1
            else:
                meetw = 0
                meetw_herh = 1
                break
    return meetw, meetw_herh


def helix(lims, process_id, output_file):
    """Export workflow information in helix table format."""
    output_file.write("<meet_id>\tOnderzoeksnummer\tmeetw_zui\tmeetw_zui_herh\tmeetw_libprep\tmeetw_libprep_herh\tmeetw_enrich\tmeetw_enrich_herh\tmeetw_seq\tmeetw_seq_herh\n")
    process = Process(lims, id=process_id)

    meetw_zui_processes = ['Dx sample registratie zuivering', 'Dx Hamilton uitvullen', 'Dx Hamilton zuiveren', 'Dx Zuiveren gDNA manueel', 'Dx gDNA Normalisatie Caliper']
    meetw_libprep_processes = ['Dx Fragmenteren & BBSS', 'Dx LibraryPrep Caliper KAPA', 'Dx Library Prep amplificatie & clean up KAPA']
    meetw_enrich_processes = ['Dx Multiplexen library prep', 'Dx Enrichment DNA fragments', 'Dx Post Enrichment clean up', 'Dx Post Enrichment PCR & clean up', 'Dx Aliquot Post Enrichment (clean)', 'Dx Aliquot Post Enrichment PCR (clean)']
    meetw_seq_processes = ['Dx Library pool verdunnen', 'Dx Multiplexen library pool', 'Dx Library pool denatureren en laden (NextSeq)', 'Dx NextSeq Run (NextSeq)', 'Dx QC controle Lab sequencen']

    for artifact in process.all_inputs():
        for sample in artifact.samples:
            sample_processes = {}
            sample_history = SampleHistory(lims=lims, sample_name=sample.name, output_artifact=artifact.id)

            for sample_artifact in sample_history.history:
                for process in sample_history.history[sample_artifact]:
                    process_name = sample_history.history[sample_artifact][process]['name']
                    if process_name in sample_processes:
                        sample_processes[process_name] += 1
                    else:
                        sample_processes[process_name] = 1

            # Determine meetw
            meetw_zui, meetw_zui_herh = determin_meetw(meetw_zui_processes, sample_processes)
            meetw_libprep, meetw_libprep_herh = determin_meetw(meetw_libprep_processes, sample_processes)
            meetw_enrich, meetw_enrich_herh = determin_meetw(meetw_enrich_processes, sample_processes)
            meetw_seq, meetw_seq_herh = determin_meetw(meetw_seq_processes, sample_processes)

            output_file.write(
                "{meet_id}\t{onderzoeksnummer}\t{meetw_zui}\t{meetw_zui_herh}\t{meetw_libprep}\t{meetw_libprep_herh}\t{meetw_enrich}\t{meetw_enrich_herh}\t{meetw_seq}\t{meetw_seq_herh}\n".format(
                    meet_id=sample.udf['Dx Meet ID'],
                    onderzoeksnummer=sample.udf['Dx Onderzoeknummer'],
                    meetw_zui=meetw_zui, meetw_zui_herh=meetw_zui_herh,
                    meetw_libprep=meetw_libprep, meetw_libprep_herh=meetw_libprep_herh,
                    meetw_enrich=meetw_enrich, meetw_enrich_herh=meetw_enrich_herh,
                    meetw_seq=meetw_seq, meetw_seq_herh=meetw_seq_herh,
                )
            )
