"""Workflow export functions."""
from genologics.entities import Process

import config
from .. import get_sequence_name


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


def helix_magnis(lims, process_id, output_file):
    """Export workflow information in helix table format (Magnis Workflow)."""
    output_file.write((
        "meet_id\twerklijst_nummer\tonderzoeknr\tmonsternummer\tZuivering OK?\tZuivering herh?\tSampleprep OK?\t"
        "Sampleprep herh?\tSequencen OK?\tSequencen herh?\tBfx analyse OK?\tSamplenaam\tvcf-file\tCNV vcf-file\n"
    ))
    process = Process(lims, id=process_id)

    for artifact in process.all_inputs():
        for sample in artifact.samples:
            # Only output samples with a 'Werklijstnummer'
            if 'Dx Werklijstnummer' in sample.udf:
                # Setup empty vars
                meetw_zui, meetw_zui_herh, meetw_sampleprep, meetw_sampleprep_herh, meetw_seq, meetw_seq_herh = [''] * 6
                sequence_name, gatk_vcf, exomedepth_vcf = [''] * 3

                # Only lookup meetw and vcf files for WES samples
                if sample.udf['Dx Stoftest code'] == config.stoftestcode_wes:
                    sample_artifacts = lims.get_artifacts(samplelimsid=sample.id, type='Analyte')
                    # Filter artifacts without parent_process
                    sample_artifacts = [
                        sample_artifact for sample_artifact in sample_artifacts if sample_artifact.parent_process
                    ]
                    # Sort artifact by parent process id
                    sample_artifacts = sorted(
                        sample_artifacts,
                        key=lambda artifact: int(artifact.parent_process.id.split('-')[-1])
                    )

                    sample_all_processes = {}
                    # reset after 'Dx Sample registratie zuivering' process
                    # this is a new import from helix, should not be counted as a repeat
                    sample_filter_processes = {}

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
                    meetw_zui, meetw_zui_herh = determin_meetw(
                        config.meetw_zui_wes_processes, sample_all_processes, repeat_cutoff
                    )
                    meetw_sampleprep, meetw_sampleprep_herh = determin_meetw(
                        config.meetw_sampleprep_wes_processes, sample_filter_processes, 2
                    )
                    meetw_seq, meetw_seq_herh = determin_meetw(
                        config.meetw_seq_wes_processes, sample_filter_processes, 2
                    )

                    # Determine vcf files
                    sequence_name = get_sequence_name(artifact)
                    gatk_vcf = ''
                    exomedepth_vcf = ''
                    if 'Dx GATK vcf' in artifact.udf:
                        gatk_vcf = artifact.udf['Dx GATK vcf']
                    elif 'Dx GATK vcf' in artifact.input_artifact_list()[0].udf:  # Look one more step back.
                        gatk_vcf = artifact.input_artifact_list()[0].udf['Dx GATK vcf']

                    if 'Dx ExomeDepth vcf' in artifact.udf:
                        exomedepth_vcf = artifact.udf['Dx ExomeDepth vcf']
                    elif 'Dx ExomeDepth vcf' in artifact.input_artifact_list()[0].udf:  # Look one more step back.
                        exomedepth_vcf = artifact.input_artifact_list()[0].udf['Dx ExomeDepth vcf']

                output_file.write((
                    "{meet_id}\t{werklijst}\t{onderzoeksnummer}\t{monsternummer}\t{meetw_zui}\t{meetw_zui_herh}\t"
                    "{meetw_sampleprep}\t{meetw_sampleprep_herh}\t{meetw_seq}\t{meetw_seq_herh}\t{meetw_bfx}\t"
                    "{sample_name}\t{vcf_file}\t{cnv_vcf_file}\n"
                ).format(
                        meet_id=sample.udf['Dx Meet ID'].split(';')[0],
                        werklijst=sample.udf['Dx Werklijstnummer'].split(';')[0],
                        onderzoeksnummer=sample.udf['Dx Onderzoeknummer'].split(';')[0],
                        monsternummer=sample.udf['Dx Monsternummer'],
                        meetw_zui=meetw_zui, meetw_zui_herh=meetw_zui_herh,
                        meetw_sampleprep=meetw_sampleprep, meetw_sampleprep_herh=meetw_sampleprep_herh,
                        meetw_seq=meetw_seq, meetw_seq_herh=meetw_seq_herh,
                        meetw_bfx='J',
                        sample_name=sequence_name,
                        vcf_file=gatk_vcf,
                        cnv_vcf_file=exomedepth_vcf,
                    )
                )


def helix_mip(lims, process_id, output_file):
    """Export workflow information in helix table format (MIP Workflow)."""
    output_file.write((
        "meet_id\twerklijst_nummer\tonderzoeknr\tmonsternummer\tLibprep OK?\tLibprep herh?\t"
        "Sequencen OK?\tSequencen herh?\tMIP bfx analyse OK?\n"
    ))
    process = Process(lims, id=process_id)

    for artifact in process.all_inputs():
        for sample in artifact.samples:
            if 'Dx Werklijstnummer' in sample.udf:  # Only check samples with a 'Werklijstnummer'
                sample_artifacts = lims.get_artifacts(samplelimsid=sample.id, type='Analyte')
                # Filter artifacts without parent_process
                sample_artifacts = [sample_artifact for sample_artifact in sample_artifacts if sample_artifact.parent_process]
                # Sort artifact by parent process id
                sample_artifacts = sorted(
                    sample_artifacts,
                    key=lambda artifact: int(artifact.parent_process.id.split('-')[-1])
                )
                # reset after 'Dx Sample registratie zuivering' process
                # this is a new import from helix, should not be counted as a repeat
                sample_filter_processes = {}

                for sample_artifact in sample_artifacts:
                    if 'Dx Sample registratie zuivering' in sample_artifact.parent_process.type.name:
                        sample_filter_processes = {}  # reset after new helix import
                    process_id = sample_artifact.parent_process.id
                    process_name = sample_artifact.parent_process.type.name

                    if process_name in sample_filter_processes:
                        sample_filter_processes[process_name].add(process_id)
                    else:
                        sample_filter_processes[process_name] = set([process_id])

                # Determine meetw
                meetw_libprep, meetw_libprep_herh = determin_meetw(
                    config.meetw_libprep_mip_processes, sample_filter_processes, 2
                )
                meetw_seq, meetw_seq_herh = determin_meetw(
                    config.meetw_seq_mip_processes, sample_filter_processes, 2
                )

                output_file.write((
                    "{meet_id}\t{werklijst}\t{onderzoeksnummer}\t{monsternummer}\t"
                    "{meetw_libprep}\t{meetw_libprep_herh}\t{meetw_seq}\t{meetw_seq_herh}\t{meetw_bfx}\n"
                ).format(
                        meet_id=sample.udf['Dx Meet ID'].split(';')[0],
                        werklijst=sample.udf['Dx Werklijstnummer'].split(';')[0],
                        onderzoeksnummer=sample.udf['Dx Onderzoeknummer'].split(';')[0],
                        monsternummer=sample.udf['Dx Monsternummer'],
                        meetw_libprep=meetw_libprep, meetw_libprep_herh=meetw_libprep_herh,
                        meetw_seq=meetw_seq, meetw_seq_herh=meetw_seq_herh,
                        meetw_bfx='J',
                    )
                )


def helix_callisto(lims, process_id, output_file):
    """Export workflow information in helix table format (Callisto srWGS Workflow).

    Args:
        lims (object): Lims connection
        process_id (str): Process ID
        output_file (file): Workflow export for Helix file path.
    """
    output_file.write((
        "meet_id\twerklijst_nummer\tonderzoeknr\tmonsternummer\tZuivering OK?\tZuivering herh?\tSampleprep OK?\t"
        "Sampleprep herh?\tSequencen OK?\tSequencen herh?\tBfx analyse OK?\tSamplenaam\tvcf-file\tCNV vcf-file\n"
    ))
    process = Process(lims, id=process_id)

    for artifact in process.all_inputs():
        for sample in artifact.samples:
            # Only output samples with a 'Werklijstnummer'
            if 'Dx Werklijstnummer' in sample.udf:
                # Setup empty vars
                meetw_zui, meetw_zui_herh, meetw_sampleprep, meetw_sampleprep_herh, meetw_seq, meetw_seq_herh = [''] * 6
                sequence_name, gatk_vcf = [''] * 2
                # Only lookup meetw and vcf files for srWGS samples
                if sample.udf['Dx Stoftest code'] == config.stoftestcode_srwgs:
                    sample_artifacts = lims.get_artifacts(samplelimsid=sample.id, type='Analyte')
                    # Filter artifacts without parent_process
                    sample_artifacts = [
                        sample_artifact for sample_artifact in sample_artifacts if sample_artifact.parent_process
                    ]
                    # Sort artifact by parent process id
                    sample_artifacts = sorted(
                        sample_artifacts,
                        key=lambda artifact: int(artifact.parent_process.id.split('-')[-1])
                    )

                    sample_all_processes = {}
                    # reset after 'Dx Sample registratie zuivering' process
                    # this is a new import from helix, should not be counted as a repeat
                    sample_filter_processes = {}

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
                    meetw_zui, meetw_zui_herh = determin_meetw(
                        config.meetw_zui_srwgs_processes, sample_all_processes, repeat_cutoff
                    )
                    meetw_sampleprep, meetw_sampleprep_herh = determin_meetw(
                        config.meetw_sampleprep_srwgs_processes, sample_filter_processes, 2
                    )
                    meetw_seq, meetw_seq_herh = determin_meetw(
                        config.meetw_seq_srwgs_processes, sample_filter_processes, 2
                    )

                    # Determine vcf files
                    sequence_name = get_sequence_name(artifact)
                    if 'Dx GATK vcf' in artifact.udf:
                        gatk_vcf = artifact.udf['Dx GATK vcf']
                    elif 'Dx GATK vcf' in artifact.input_artifact_list()[0].udf:  # Look one more step back.
                        gatk_vcf = artifact.input_artifact_list()[0].udf['Dx GATK vcf']

                output_file.write((
                    "{meet_id}\t{werklijst}\t{onderzoeksnummer}\t{monsternummer}\t{meetw_zui}\t{meetw_zui_herh}\t"
                    "{meetw_sampleprep}\t{meetw_sampleprep_herh}\t{meetw_seq}\t{meetw_seq_herh}\t{meetw_bfx}\t"
                    "{sample_name}\t{vcf_file}\t{cnv_vcf_file}\n"
                ).format(
                        meet_id=sample.udf['Dx Meet ID'].split(';')[0],
                        werklijst=sample.udf['Dx Werklijstnummer'].split(';')[0],
                        onderzoeksnummer=sample.udf['Dx Onderzoeknummer'].split(';')[0],
                        monsternummer=sample.udf['Dx Monsternummer'],
                        meetw_zui=meetw_zui, meetw_zui_herh=meetw_zui_herh,
                        meetw_sampleprep=meetw_sampleprep, meetw_sampleprep_herh=meetw_sampleprep_herh,
                        meetw_seq=meetw_seq, meetw_seq_herh=meetw_seq_herh,
                        meetw_bfx='J',
                        sample_name=sequence_name,
                        vcf_file=gatk_vcf,
                        cnv_vcf_file='',
                    )
                )
