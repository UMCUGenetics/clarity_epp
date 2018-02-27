"""Workflow export functions."""
from sets import Set

from genologics.entities import Process

import config


def determin_meetw(meetw_processes, sample_processes):
    """Determine meetw and meetw_herh based on list of processes."""
    meetw = 0
    meetw_herh = 0

    for process in meetw_processes:
        if process in sample_processes:
            if len(sample_processes[process]) == 1:
                meetw = 1
            else:
                meetw = 0
                meetw_herh = 1
                break
    return meetw, meetw_herh


def helix(lims, process_id, output_file):
    """Export workflow information in helix table format."""
    output_file.write("<meet_id>\tOnderzoeksnummer\tMonsternummer\tWerklijst\tmeetw_zui\tmeetw_zui_herh\tmeetw_libprep\tmeetw_libprep_herh\tmeetw_enrich\tmeetw_enrich_herh\tmeetw_seq\tmeetw_seq_herh\n")
    process = Process(lims, id=process_id)

    for artifact in process.all_inputs():
        for sample in artifact.samples:
            sample_artifacts = lims.get_artifacts(samplelimsid=sample.id)
            sample_processes = {}

            for artifact in sample_artifacts:
                if artifact.parent_process:
                    process_id = artifact.parent_process.id
                    process_name = artifact.parent_process.type.name
                    if process_name in sample_processes:
                        sample_processes[process_name].add(process_id)
                    else:
                        sample_processes[process_name] = Set([process_id])

            # Determine meetw
            meetw_zui, meetw_zui_herh = determin_meetw(config.meetw_zui_processes, sample_processes)
            meetw_libprep, meetw_libprep_herh = determin_meetw(config.meetw_libprep_processes, sample_processes)
            meetw_enrich, meetw_enrich_herh = determin_meetw(config.meetw_enrich_processes, sample_processes)
            meetw_seq, meetw_seq_herh = determin_meetw(config.meetw_seq_processes, sample_processes)

            output_file.write(
                "{meet_id}\t{onderzoeksnummer}\t{monsternummer}\t{werklijst}\t{meetw_zui}\t{meetw_zui_herh}\t{meetw_libprep}\t{meetw_libprep_herh}\t{meetw_enrich}\t{meetw_enrich_herh}\t{meetw_seq}\t{meetw_seq_herh}\n".format(
                    meet_id=sample.udf['Dx Meet ID'],
                    onderzoeksnummer=sample.udf['Dx Onderzoeknummer'],
                    monsternummer=sample.udf['Dx Monsternummer'],
                    werklijst=sample.udf['Dx Werklijstnummer'],
                    meetw_zui=meetw_zui, meetw_zui_herh=meetw_zui_herh,
                    meetw_libprep=meetw_libprep, meetw_libprep_herh=meetw_libprep_herh,
                    meetw_enrich=meetw_enrich, meetw_enrich_herh=meetw_enrich_herh,
                    meetw_seq=meetw_seq, meetw_seq_herh=meetw_seq_herh,
                )
            )
