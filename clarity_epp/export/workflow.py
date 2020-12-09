"""Workflow export functions."""
from genologics.entities import Process

import config


def determin_meetw(meetw_processes, sample_processes, repeat_cutoff=2):
    """Determine meetwaarde and meetwaarde herhaling (reapeat) based on list of processes and repeat cutoff."""
    meetw = 'N'
    meetw_herh = 'N'

    for process in meetw_processes:
        if process in sample_processes:
            if len(sample_processes[process]) >= repeat_cutoff:
                meetw = 'N'
                meetw_herh = 'J'
                break
            else:
                meetw = 'J'
    return meetw, meetw_herh


def helix_lab(lims, process_id, output_file):
    """Export lab workflow information in helix table format."""
    output_file.write("meet_id\twerklijst_nummer\tonderzoeknr\tmonsternummer\tZuivering OK?\tZuivering herh?\tLibprep OK?\tLibprep herh?\tEnrichment OK?\tEnrichment herh?\tSequencen OK?\tSequencen herh?\n")
    process = Process(lims, id=process_id)

    for artifact in process.all_inputs():
        for sample in artifact.samples:
            if 'Dx Werklijstnummer' in sample.udf:  # Only check samples with a 'Werklijstnummer'
                sample_artifacts = lims.get_artifacts(samplelimsid=sample.id, type='Analyte')
                sample_artifacts = [sample_artifact for sample_artifact in sample_artifacts if sample_artifact.parent_process]  # Filter artifacts without parent_process
                sample_artifacts = sorted(sample_artifacts, key=lambda artifact: int(artifact.parent_process.id.split('-')[-1]))  # Sort artifact by parent process id 
                
                sample_all_processes = {}
                sample_filter_processes = {}  # reset after Dx Sample registratie zuivering

                for artifact in sample_artifacts:
                    if 'Dx Sample registratie zuivering' in artifact.parent_process.type.name:
                        sample_filter_processes = {}  # reset after new helix import
                    process_id = artifact.parent_process.id
                    process_name = artifact.parent_process.type.name

                    if process_name in sample_all_processes:
                        sample_all_processes[process_name].add(process_id)
                    else:
                        sample_all_processes[process_name] = set([process_id])

                    if process_name in sample_filter_processes:
                        sample_filter_processes[process_name].add(process_id)
                    else:
                        sample_filter_processes[process_name] = set([process_id])

                # Determine meetw
                repeat_cutoff = len(sample.udf['Dx Werklijstnummer'].split(';')) * 2
                meetw_zui, meetw_zui_herh = determin_meetw(config.meetw_zui_processes, sample_all_processes, repeat_cutoff)
                meetw_libprep, meetw_libprep_herh = determin_meetw(config.meetw_libprep_processes, sample_filter_processes, 2)
                meetw_enrich, meetw_enrich_herh = determin_meetw(config.meetw_enrich_processes, sample_filter_processes, 2)
                meetw_seq, meetw_seq_herh = determin_meetw(config.meetw_seq_processes, sample_filter_processes, 2)

                output_file.write(
                    "{meet_id}\t{werklijst}\t{onderzoeksnummer}\t{monsternummer}\t{meetw_zui}\t{meetw_zui_herh}\t{meetw_libprep}\t{meetw_libprep_herh}\t{meetw_enrich}\t{meetw_enrich_herh}\t{meetw_seq}\t{meetw_seq_herh}\n".format(
                        meet_id=sample.udf['Dx Meet ID'].split(';')[0],
                        werklijst=sample.udf['Dx Werklijstnummer'].split(';')[0],
                        onderzoeksnummer=sample.udf['Dx Onderzoeknummer'].split(';')[0],
                        monsternummer=sample.udf['Dx Monsternummer'],
                        meetw_zui=meetw_zui, meetw_zui_herh=meetw_zui_herh,
                        meetw_libprep=meetw_libprep, meetw_libprep_herh=meetw_libprep_herh,
                        meetw_enrich=meetw_enrich, meetw_enrich_herh=meetw_enrich_herh,
                        meetw_seq=meetw_seq, meetw_seq_herh=meetw_seq_herh,
                    )
                )


def helix_data_analysis(lims, process_id, output_file):
    """Export data analysis workflow information in helix table format."""
    output_file.write("meet_id\twerklijst_nummer\tonderzoeknr\tmonsternummer\tBfx analyse OK?\tSNP match OK?\n")
    process = Process(lims, id=process_id)

    for artifact in process.analytes()[0]:
        # Set SNP match meetw
        meetw_snp_match = 'N'
        if 'Dx SNPmatch' in list(artifact.udf) and artifact.udf['Dx SNPmatch']:
            meetw_snp_match = 'J'

        # Print meetw row
        for sample in artifact.samples:
            output_file.write(
                "{meet_id}\t{werklijst}\t{onderzoeksnummer}\t{monsternummer}\t{meetw_bfx}\t{meetw_snp_match}\n".format(
                    meet_id=sample.udf['Dx Meet ID'].split(';')[0],
                    werklijst=sample.udf['Dx Werklijstnummer'].split(';')[0],
                    onderzoeksnummer=sample.udf['Dx Onderzoeknummer'].split(';')[0],
                    monsternummer=sample.udf['Dx Monsternummer'],
                    meetw_bfx='J',
                    meetw_snp_match=meetw_snp_match,

                )
            )

def helix_all(lims, process_id, output_file):
    """Export workflow information in helix table format."""
    output_file.write("meet_id\twerklijst_nummer\tonderzoeknr\tmonsternummer\tZuivering OK?\tZuivering herh?\tLibprep OK?\tLibprep herh?\tEnrichment OK?\tEnrichment herh?\tSequencen OK?\tSequencen herh?\tBfx analyse OK?\tSNP match OK?\n")
    process = Process(lims, id=process_id)

    for artifact in process.analytes()[0]:
        for sample in artifact.samples:
            if 'Dx Werklijstnummer' in sample.udf:  # Only check samples with a 'Werklijstnummer'
                sample_artifacts = lims.get_artifacts(samplelimsid=sample.id, type='Analyte')
                sample_artifacts = [sample_artifact for sample_artifact in sample_artifacts if sample_artifact.parent_process]  # Filter artifacts without parent_process
                sample_artifacts = sorted(sample_artifacts, key=lambda artifact: int(artifact.parent_process.id.split('-')[-1]))  # Sort artifact by parent process id 
                
                sample_all_processes = {}
                sample_filter_processes = {}  # reset after 'Dx Sample registratie zuivering' process -> this is a new import from helix, should not be counted as a repeat

                for sample_artifact in sample_artifacts:
                    if 'Dx Sample registratie zuivering' in sample_artifact.parent_process.type.name:
                        sample_filter_processes = {}  # reset after new helix import
                    process_id = sample_artifact.parent_process.id
                    process_name = sample_artifact.parent_process.type.name

                    if process_name in sample_all_processes:
                        sample_all_processes[process_name].add(process_id)
                    else:
                        sample_all_processes[process_name] = set([process_id])

                    if process_name in sample_filter_processes:
                        sample_filter_processes[process_name].add(process_id)
                    else:
                        sample_filter_processes[process_name] = set([process_id])

                # Determine meetw
                repeat_cutoff = len(sample.udf['Dx Werklijstnummer'].split(';')) * 2
                meetw_zui, meetw_zui_herh = determin_meetw(config.meetw_zui_processes, sample_all_processes, repeat_cutoff)
                meetw_libprep, meetw_libprep_herh = determin_meetw(config.meetw_libprep_processes, sample_filter_processes, 2)
                meetw_enrich, meetw_enrich_herh = determin_meetw(config.meetw_enrich_processes, sample_filter_processes, 2)
                meetw_seq, meetw_seq_herh = determin_meetw(config.meetw_seq_processes, sample_filter_processes, 2)
                
                meetw_snp_match = 'N'
                if 'Dx SNPmatch' in list(artifact.udf) and artifact.udf['Dx SNPmatch']:
                    meetw_snp_match = 'J'

                output_file.write(
                    "{meet_id}\t{werklijst}\t{onderzoeksnummer}\t{monsternummer}\t{meetw_zui}\t{meetw_zui_herh}\t{meetw_libprep}\t{meetw_libprep_herh}\t{meetw_enrich}\t{meetw_enrich_herh}\t{meetw_seq}\t{meetw_seq_herh}\t{meetw_bfx}\t{meetw_snp_match}\n".format(
                        meet_id=sample.udf['Dx Meet ID'].split(';')[0],
                        werklijst=sample.udf['Dx Werklijstnummer'].split(';')[0],
                        onderzoeksnummer=sample.udf['Dx Onderzoeknummer'].split(';')[0],
                        monsternummer=sample.udf['Dx Monsternummer'],
                        meetw_zui=meetw_zui, meetw_zui_herh=meetw_zui_herh,
                        meetw_libprep=meetw_libprep, meetw_libprep_herh=meetw_libprep_herh,
                        meetw_enrich=meetw_enrich, meetw_enrich_herh=meetw_enrich_herh,
                        meetw_seq=meetw_seq, meetw_seq_herh=meetw_seq_herh,
                        meetw_bfx='J',
                        meetw_snp_match=meetw_snp_match,
                    )
                )
