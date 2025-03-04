#!venv/bin/python
"""Clarity epp application."""

import sys
import argparse

import genologics.lims
from tenacity import Retrying, RetryError, stop_after_attempt, wait_fixed

import clarity_epp.upload
import clarity_epp.export
import clarity_epp.qc
import clarity_epp.placement

import config

# Setup lims connection and try connection twice
lims = genologics.lims.Lims(config.baseuri, config.username, config.password)
genologics.lims.TIMEOUT = config.api_timeout

try:
    for lims_connection_attempt in Retrying(stop=stop_after_attempt(2), wait=wait_fixed(1)):
        with lims_connection_attempt:
            lims.check_version()
except RetryError:
    raise Exception('Could not connect to Clarity LIMS.')


# Export Functions
def export_bioanalyzer(args):
    """Export samplesheets for Bioanalyzer machine."""
    clarity_epp.export.bioanalyzer.samplesheet(lims, args.process_id, args.output_file)


def export_caliper(args):
    """Export samplesheets for caliper machine."""
    if args.type == 'normalise':
        clarity_epp.export.caliper.samplesheet_normalise(lims, args.process_id, args.output_file)
    elif args.type == 'dilute':
        clarity_epp.export.caliper.samplesheet_dilute(lims, args.process_id, args.output_file)


def export_email(args):
    """Export emails"""
    if args.type == 'sequencing_run':
        clarity_epp.export.email.sequencing_run(lims, config.email, args.process_id)


def export_hamilton(args):
    """Export samplesheets for hamilton machine."""
    if args.type == 'filling_out':
        clarity_epp.export.hamilton.samplesheet_filling_out(lims, args.process_id, args.output_file)
    elif args.type == 'purify':
        clarity_epp.export.hamilton.samplesheet_purify(lims, args.process_id, args.output_file)


def export_illumina(args):
    """Export (updated) illumina samplesheet."""
    clarity_epp.export.illumina.create_samplesheet(
        lims, args.process_id, args.output_file
    )


def export_labels(args):
    """Export container labels."""
    if args.type == 'container':
        clarity_epp.export.labels.container(lims, args.process_id, args.output_file, args.description)
    elif args.type == 'container_sample':
        clarity_epp.export.labels.container_sample(lims, args.process_id, args.output_file, args.description)
    elif args.type == 'storage_location':
        clarity_epp.export.labels.storage_location(lims, args.process_id, args.output_file)
    elif args.type == 'nunc_mix_sample':
        clarity_epp.export.labels.nunc_mix_sample(lims, args.process_id, args.output_file)
    elif args.type == 'strips_callisto':
        clarity_epp.export.labels.strips_callisto(lims, args.process_id, args.output_file)


def export_magnis(args):
    """Export magnis samplesheet."""
    clarity_epp.export.magnis.samplesheet(lims, args.process_id, args.output_file)


def export_manual_pipetting(args):
    """Export samplesheets for manual pipetting."""
    if args.type == 'purify':
        clarity_epp.export.manual_pipetting.samplesheet_purify(lims, args.process_id, args.output_file)
    elif args.type == 'dilute_library_pool':
        clarity_epp.export.manual_pipetting.samplesheet_dilute_library_pool(lims, args.process_id, args.output_file)
    elif args.type == 'multiplex_library_pool':
        clarity_epp.export.manual_pipetting.samplesheet_multiplex_library_pool(lims, args.process_id, args.output_file)
    elif args.type == 'multiplex_sequence_pool':
        clarity_epp.export.manual_pipetting.samplesheet_multiplex_sequence_pool(lims, args.process_id, args.output_file)
    elif args.type == 'normalization':
        clarity_epp.export.manual_pipetting.samplesheet_normalization(lims, args.process_id, args.output_file)
    elif args.type == 'capture':
        clarity_epp.export.manual_pipetting.samplesheet_capture(lims, args.process_id, args.output_file)
    elif args.type == 'exonuclease':
        clarity_epp.export.manual_pipetting.sammplesheet_exonuclease(lims, args.process_id, args.output_file)
    elif args.type == 'pcr_exonuclease':
        clarity_epp.export.manual_pipetting.sammplesheet_pcr_exonuclease(lims, args.process_id, args.output_file)
    elif args.type == 'mip_multiplex_pool':
        clarity_epp.export.manual_pipetting.samplesheet_mip_multiplex_pool(lims, args.process_id, args.output_file)
    elif args.type == 'mip_dilute_pool':
        clarity_epp.export.manual_pipetting.samplesheet_mip_pool_dilution(lims, args.process_id, args.output_file)
    elif args.type == 'pool_samples':
        clarity_epp.export.manual_pipetting.samplesheet_pool_samples(lims, args.process_id, args.output_file)
    elif args.type == 'pool_magnis_pools':
        clarity_epp.export.manual_pipetting.samplesheet_pool_magnis_pools(lims, args.process_id, args.output_file)
    elif args.type == 'normalization_mix':
        clarity_epp.export.manual_pipetting.samplesheet_normalization_mix(lims, args.process_id, args.output_file)


def export_merge_file(args):
    """Export merge file."""
    clarity_epp.export.merge.create_file(lims, args.process_id, args.output_file)


def export_myra(args):
    """Export myra samplesheet."""
    if args.type == 'to_callisto':
        clarity_epp.export.myra.samplesheet_to_callisto(lims, args.process_id, args.output_file)
    elif args.type == 'from_callisto':
        clarity_epp.export.myra.samplesheet_from_callisto(lims, args.process_id, args.output_file)


def export_ped_file(args):
    """Export ped file."""
    clarity_epp.export.ped.create_file(lims, args.process_id, args.output_file)


def export_removed_samples(args):
    """Export removed samples table."""
    clarity_epp.export.sample.removed_samples(lims, args.output_file)


def export_sample_udf_dx(args):
    "Export table sample udf (Dx-udf only)"""
    clarity_epp.export.sample.sample_udf_dx(
        lims,
        args.output_file,
        args.artifact_name,
        args.sequencing_run,
        args.sequencing_run_project,
        args.udf,
        args.column_name
    )


def export_sample_related_mip(args):
    """Export related MIP samples"""
    clarity_epp.export.sample.sample_related_mip(lims, args.process_id, args.output_file)


def export_tapestation(args):
    """Export samplesheets for Tapestation machine."""
    clarity_epp.export.tapestation.samplesheet(lims, args.process_id, args.output_file)


def export_tecan(args):
    """Export samplesheets for tecan machine."""
    clarity_epp.export.tecan.samplesheet(lims, args.process_id, args.type, args.output_file)


def export_workflow(args):
    """Export workflow overview files."""
    if args.type == 'magnis':
        clarity_epp.export.workflow.helix_magnis(lims, args.process_id, args.output_file)
    elif args.type == 'mip':
        clarity_epp.export.workflow.helix_mip(lims, args.process_id, args.output_file)
    elif args.type == 'callisto':
        clarity_epp.export.workflow.helix_callisto(lims, args.process_id, args.output_file)


# Upload Functions
def upload_samples(args):
    """Upload samples from helix output file."""
    clarity_epp.upload.samples.from_helix(lims, config.email, args.input_file)


def upload_tecan_results(args):
    """Upload tecan results."""
    if args.type == 'qc':
        clarity_epp.upload.tecan.results_qc(lims, args.process_id)
    elif args.type == 'purify_normalise':
        clarity_epp.upload.tecan.results_purify_normalise(lims, args.process_id)
    elif args.type == 'purify_mix':
        clarity_epp.upload.tecan.results_purify_mix(lims, args.process_id)


def upload_tapestation_results(args):
    """Upload tapestation results."""
    clarity_epp.upload.tapestation.results(lims, args.process_id)


def upload_bioanalyzer_results(args):
    """Upload bioanalyzer results."""
    clarity_epp.upload.bioanalyzer.results(lims, args.process_id)


def upload_magnis_results(args):
    """Upload magnis results."""
    clarity_epp.upload.magnis.results(lims, args.process_id)


# QC functions
def qc_fragment_length(args):
    """Set QC status based on fragment length measurement."""
    clarity_epp.qc.fragment_length.set_qc_flag(lims, args.process_id)


def qc_illumina(args):
    """Set average % Bases >=Q30."""
    clarity_epp.qc.illumina.set_avg_q30(lims, args.process_id)


def qc_qubit(args):
    """Set QC status based on qubit measurement."""
    clarity_epp.qc.qubit.set_qc_flag(lims, args.process_id)


def qc_sample_mip(args):
    """Set mip data ready udf for wes samples from same person and test."""
    clarity_epp.qc.sample.set_mip_data_ready(lims, args.process_id)


# Placement functions
def placement_automatic(args):
    """Copy container layout from previous step."""
    clarity_epp.placement.plate.copy_layout(lims, args.process_id)


def placement_artifact_set(args):
    """Change artifact name or udf."""
    if args.type == 'sequence_name':
        clarity_epp.placement.artifact.set_sequence_name(lims, args.process_id)
    elif args.type == 'run_id':
        clarity_epp.placement.artifact.set_runid_name(lims, args.process_id)
    elif args.type == 'norm_udf':
        clarity_epp.placement.artifact.set_norm_manual_udf(lims, args.process_id)


def placement_route_artifact(args):
    """Route artifacts to a workflow"""
    clarity_epp.placement.artifact.route_to_workflow(lims, args.process_id, args.workflow)


def placement_barcode(args):
    """Check barcodes."""
    if args.type == 'check_family':
        clarity_epp.placement.barcode.check_family(lims, args.process_id)


def placement_unpooling(args):
    """Pool unpooling."""
    clarity_epp.placement.pool.unpooling(lims, args.process_id)


def placement_patient_pools(args):
    """Create  patient pools for Dx samples."""
    clarity_epp.placement.pool.create_patient_pools(lims, args.process_id)


def placement_complete_step(args):
    """Complete protocol step (Dx Mark protocol complete)."""
    clarity_epp.placement.step.finish_protocol_complete(lims, args.process_id)


def placement_tecan(args):
    """Placement tecan process, distribute artifacts over two containers"""
    clarity_epp.placement.tecan.place_artifacts(lims, args.process_id)


def placement_pipetting(args):
    """Check pipetted input and output nuncs."""
    clarity_epp.placement.pipetting.check_nunc_input_nunc_output(lims, args.process_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers()

    output_parser = argparse.ArgumentParser(add_help=False)
    output_parser.add_argument(
        '-o', '--output_file',  nargs='?', type=argparse.FileType('w'), default=sys.stdout,
        help='Output file path (default=stdout)'
    )

    # export
    parser_export = subparser.add_parser('export', help='Export from lims')
    subparser_export = parser_export.add_subparsers()

    parser_export_bioanalyzer = subparser_export.add_parser(
        'bioanalyzer', help='Create bioanalyzer samplesheets', parents=[output_parser]
    )
    parser_export_bioanalyzer.add_argument('process_id', help='Clarity lims process id')
    parser_export_bioanalyzer.set_defaults(func=export_bioanalyzer)

    parser_export_caliper = subparser_export.add_parser('caliper', help='Create caliper samplesheets', parents=[output_parser])
    parser_export_caliper.add_argument('type', choices=['normalise', 'dilute'], help='Samplesheet type')
    parser_export_caliper.add_argument('process_id', help='Clarity lims process id')
    parser_export_caliper.set_defaults(func=export_caliper)

    parser_export_email = subparser_export.add_parser('email', help='Send emails', parents=[output_parser])
    parser_export_email.add_argument('type', choices=['sequencing_run'], help='Email type')
    parser_export_email.add_argument('process_id', help='Clarity lims process id')
    parser_export_email.set_defaults(func=export_email)

    parser_export_hamilton = subparser_export.add_parser(
        'hamilton', help='Create hamilton samplesheets', parents=[output_parser]
    )
    parser_export_hamilton.add_argument('type', choices=['filling_out', 'purify'], help='Samplesheet type')
    parser_export_hamilton.add_argument('process_id', help='Clarity lims process id')
    parser_export_hamilton.set_defaults(func=export_hamilton)

    parser_export_illumina = subparser_export.add_parser(
        'illumina', help='Export illumina samplesheet', parents=[output_parser]
    )
    parser_export_illumina.add_argument('process_id', help='Clarity lims process id')
    parser_export_illumina.set_defaults(func=export_illumina)

    parser_export_labels = subparser_export.add_parser('labels', help='Export container labels', parents=[output_parser])
    parser_export_labels.add_argument(
        'type',
        choices=['container', 'container_sample', 'storage_location', 'nunc_mix_sample', 'strips_callisto'],
        help='Label type')
    parser_export_labels.add_argument('process_id', help='Clarity lims process id')
    parser_export_labels.add_argument('-d', '--description',  nargs='?', help='Container name description')
    parser_export_labels.set_defaults(func=export_labels)

    parser_export_magnis = subparser_export.add_parser(
        'magnis', help='Export magnis samplesheet', parents=[output_parser]
    )
    parser_export_magnis.add_argument('process_id', help='Clarity lims process id')
    parser_export_magnis.set_defaults(func=export_magnis)

    parser_export_manual_pipetting = subparser_export.add_parser(
        'manual', help='Create manual pipetting exports', parents=[output_parser]
    )
    parser_export_manual_pipetting.add_argument(
        'type',
        choices=[
            'purify', 'dilute_library_pool', 'multiplex_library_pool', 'multiplex_sequence_pool', 'normalization',
            'capture', 'exonuclease', 'pcr_exonuclease', 'mip_multiplex_pool', 'mip_dilute_pool', 'pool_samples',
            'pool_magnis_pools', 'normalization_mix'
        ],
        help='Samplesheet type'
    )
    parser_export_manual_pipetting.add_argument('process_id', help='Clarity lims process id')
    parser_export_manual_pipetting.set_defaults(func=export_manual_pipetting)

    parser_export_merge = subparser_export.add_parser('merge', help='Export merge file', parents=[output_parser])
    parser_export_merge.add_argument('process_id', help='Clarity lims process id')
    parser_export_merge.set_defaults(func=export_merge_file)

    parser_export_myra = subparser_export.add_parser('myra', help='Export myra samplesheet', parents=[output_parser])
    parser_export_myra.add_argument('type', choices=['to_callisto', 'from_callisto'], help='Samplesheet type')
    parser_export_myra.add_argument('process_id', help='Clarity lims process id')
    parser_export_myra.set_defaults(func=export_myra)

    parser_export_ped = subparser_export.add_parser('ped', help='Export ped file', parents=[output_parser])
    parser_export_ped.add_argument('process_id', help='Clarity lims process id')
    parser_export_ped.set_defaults(func=export_ped_file)

    parser_export_removed_samples = subparser_export.add_parser(
        'removed_samples', help='Export removed samples table', parents=[output_parser]
    )
    parser_export_removed_samples.set_defaults(func=export_removed_samples)

    parser_export_sample_udf_dx = subparser_export.add_parser(
        'sample_udf_dx', help='Export sample udf table (Dx-udf only).', parents=[output_parser]
    )
    parser_export_sample_udf_dx_group = parser_export_sample_udf_dx.add_mutually_exclusive_group(required=True)
    parser_export_sample_udf_dx_group.add_argument('-a', '--artifact_name', help='Artifact name')
    parser_export_sample_udf_dx_group.add_argument('-r', '--sequencing_run', help='Sequencing run name')
    parser_export_sample_udf_dx.add_argument(
        '-p', '--sequencing_run_project',  nargs='?', help='Sequencing run project name'
    )
    parser_export_sample_udf_dx.add_argument('-u', '--udf', help='udf to query (limited to only Dx-udf)')
    parser_export_sample_udf_dx.add_argument('-c', '--column_name', help='naming of column')
    parser_export_sample_udf_dx.set_defaults(func=export_sample_udf_dx)

    parser_export_sample_related_mip = subparser_export.add_parser(
        'sample_related_mip', help='Export related mip samples.', parents=[output_parser]
    )
    parser_export_sample_related_mip.add_argument('process_id', help='Clarity lims process id')
    parser_export_sample_related_mip.set_defaults(func=export_sample_related_mip)

    parser_export_tapestation = subparser_export.add_parser(
        'tapestation', help='Create tapestation samplesheets', parents=[output_parser]
    )
    parser_export_tapestation.add_argument('process_id', help='Clarity lims process id')
    parser_export_tapestation.set_defaults(func=export_tapestation)

    parser_export_tecan = subparser_export.add_parser('tecan', help='Create tecan samplesheets', parents=[output_parser])
    parser_export_tecan.add_argument('process_id', help='Clarity lims process id')
    parser_export_tecan.add_argument(
        'type', choices=['qc', 'purify_normalise', 'filling_out_purify', 'normalise'], help='Samplesheet type'
    )
    parser_export_tecan.set_defaults(func=export_tecan)

    parser_export_workflow = subparser_export.add_parser(
        'workflow', help='Export workflow result file', parents=[output_parser]
    )
    parser_export_workflow.add_argument('type', choices=['magnis', 'mip', 'callisto'], help='Workflow type')
    parser_export_workflow.add_argument('process_id', help='Clarity lims process id')
    parser_export_workflow.set_defaults(func=export_workflow)

    # Sample upload
    parser_upload = subparser.add_parser('upload', help='Upload samples or results to clarity lims')
    subparser_upload = parser_upload.add_subparsers()

    parser_upload_bioanalyzer = subparser_upload.add_parser('bioanalyzer', help='Upload bioanalyzer results')
    parser_upload_bioanalyzer.add_argument('process_id', help='Clarity lims process id')
    parser_upload_bioanalyzer.set_defaults(func=upload_bioanalyzer_results)

    parser_upload_sample = subparser_upload.add_parser('sample', help='Upload samples from helix export')
    parser_upload_sample.add_argument('input_file', type=argparse.FileType('r'), help='Input file path')
    parser_upload_sample.set_defaults(func=upload_samples)

    parser_upload_tapestation = subparser_upload.add_parser('tapestation', help='Upload tapestation results')
    parser_upload_tapestation.add_argument('process_id', help='Clarity lims process id')
    parser_upload_tapestation.set_defaults(func=upload_tapestation_results)

    parser_upload_tecan = subparser_upload.add_parser('tecan', help='Upload tecan results')
    parser_upload_tecan.add_argument('process_id', help='Clarity lims process id')
    parser_upload_tecan.add_argument('type', choices=['qc', 'purify_normalise', 'purify_mix'], help='Tecan process type')
    parser_upload_tecan.set_defaults(func=upload_tecan_results)

    parser_upload_magnis = subparser_upload.add_parser('magnis', help='Upload magnis results')
    parser_upload_magnis.add_argument('process_id', help='Clarity lims process id')
    parser_upload_magnis.set_defaults(func=upload_magnis_results)

    # QC
    parser_qc = subparser.add_parser('qc', help='Set QC values/flags')
    subparser_qc = parser_qc.add_subparsers()

    parser_qc_fragment_length = subparser_qc.add_parser('fragment_length', help='Set fragment length qc flag')
    parser_qc_fragment_length.add_argument('process_id', help='Clarity lims process id')
    parser_qc_fragment_length.set_defaults(func=qc_fragment_length)

    parser_qc_illumina = subparser_qc.add_parser('illumina', help='Set average % Bases >=Q30')
    parser_qc_illumina.add_argument('process_id', help='Clarity lims process id')
    parser_qc_illumina.set_defaults(func=qc_illumina)

    parser_qc_qubit = subparser_qc.add_parser('qubit', help='Set qubit qc flag')
    parser_qc_qubit.add_argument('process_id', help='Clarity lims process id')
    parser_qc_qubit.set_defaults(func=qc_qubit)

    parser_qc_sample_mip = subparser_qc.add_parser(
        'sample_mip', help='Set mip data ready udf for wes samples from same person and test.'
    )
    parser_qc_sample_mip.add_argument('process_id', help='Clarity lims process id')
    parser_qc_sample_mip.set_defaults(func=qc_sample_mip)

    # placement
    parser_placement = subparser.add_parser('placement', help='Container placement functions')
    subparser_placement = parser_placement.add_subparsers()

    parser_placement_automatic = subparser_placement.add_parser('copy', help='Copy container layout from previous step')
    parser_placement_automatic.add_argument('process_id', help='Clarity lims process id')
    parser_placement_automatic.set_defaults(func=placement_automatic)

    parser_placement_artifact = subparser_placement.add_parser('artifact', help='Change artifact name to sequence name')
    parser_placement_artifact.add_argument('type', choices=['sequence_name', 'run_id', 'norm_udf'], help='Check type')
    parser_placement_artifact.add_argument('process_id', help='Clarity lims process id')
    parser_placement_artifact.set_defaults(func=placement_artifact_set)

    parser_placement_route_artifact = subparser_placement.add_parser('route_artifact', help='Route artifact to a workflow')
    parser_placement_route_artifact.add_argument('process_id', help='Clarity lims process id')
    parser_placement_route_artifact.add_argument('workflow', choices=['post_bioinf', 'sequencing'], help='Workflow')
    parser_placement_route_artifact.set_defaults(func=placement_route_artifact)

    parser_placement_barcode = subparser_placement.add_parser('barcode_check', help='Check barcode clarity_epp.placement')
    parser_placement_barcode.add_argument('type', choices=['check_family'], help='Check type')
    parser_placement_barcode.add_argument('process_id', help='Clarity lims process id')
    parser_placement_barcode.set_defaults(func=placement_barcode)

    parser_placement_complete_step = subparser_placement.add_parser(
        'complete_step', help='Complete step Dx Mark protocol complete'
    )
    parser_placement_complete_step.add_argument('process_id', help='Clarity lims process id')
    parser_placement_complete_step.set_defaults(func=placement_complete_step)

    parser_placement_unpooling = subparser_placement.add_parser('unpooling', help='Unpooling of sequencing pool')
    parser_placement_unpooling.add_argument('process_id', help='Clarity lims process id')
    parser_placement_unpooling.set_defaults(func=placement_unpooling)

    parser_placement_patient_pools = subparser_placement.add_parser(
        'patient_pools', help='Create patient pools for Dx samples'
    )
    parser_placement_patient_pools.add_argument('process_id', help='Clarity lims process id')
    parser_placement_patient_pools.set_defaults(func=placement_patient_pools)

    parser_placement_tecan = subparser_placement.add_parser('tecan', help='Placement of samples in tecan step')
    parser_placement_tecan.add_argument('process_id', help='Clarity lims process id')
    parser_placement_tecan.set_defaults(func=placement_tecan)

    parser_placement_pipetting = subparser_placement.add_parser('pipetting', help='Check pipetting input and output')
    parser_placement_pipetting.add_argument('process_id', help='Clarity lims process id')
    parser_placement_pipetting.set_defaults(func=placement_pipetting)

    args = parser.parse_args()
    args.func(args)
