#!venv/bin/python
"""Clarity epp application."""

import sys
import argparse

from genologics.lims import Lims


import clarity_epp.upload
import clarity_epp.export
import clarity_epp.qc
import clarity_epp.placement
import clarity_epp.generate

import config

# Setup lims connection
lims = Lims(config.baseuri, config.username, config.password)


# Export Functions
def export_bioanalyzer(args):
    """Export samplesheets for Bioanalyzer machine."""
    clarity_epp.export.bioanalyzer.samplesheet(lims, args.process_id, args.output_file)


def export_caliper(args):
    """Export samplesheets for caliper machine."""
    if args.type == 'normalise':
        clarity_epp.export.caliper.samplesheet_normalise(lims, args.process_id, args.output_file)


def export_hamilton(args):
    """Export samplesheets for hamilton machine."""
    if args.type == 'filling_out':
        clarity_epp.export.hamilton.samplesheet_filling_out(lims, args.process_id, args.output_file)
    elif args.type == 'purify':
        clarity_epp.export.hamilton.samplesheet_purify(lims, args.process_id, args.output_file)


def export_labels(args):
    """Export container labels."""
    clarity_epp.export.labels.containers(lims, args.process_id, args.output_file)


def export_manual_pipetting(args):
    """Export samplesheets for manual pipetting."""
    if args.type == 'purify':
        clarity_epp.export.manual_pipetting.samplesheet_purify(lims, args.process_id, args.output_file)
    elif args.type == 'sequencing_pool':
        clarity_epp.export.manual_pipetting.samplesheet_sequencing_pool(lims, args.process_id, args.output_file)
    elif args.type == 'multiplex':
        clarity_epp.export.manual_pipetting.samplesheet_multiplex(lims, args.process_id, args.output_file)


def export_ped_file(args):
    """Export ped file."""
    clarity_epp.export.ped.create_file(lims, args.process_id, args.output_file)


def export_tapestation(args):
    """Export samplesheets for Tapestation machine."""
    clarity_epp.export.tapestation.samplesheet(lims, args.process_id, args.output_file)


def export_tecan(args):
    """Export samplesheets for tecan machine."""
    clarity_epp.export.tecan.samplesheet(lims, args.process_id, args.output_file)


# Upload Functions
def upload_samples(args):
    """Upload samples from helix output file."""
    clarity_epp.upload.samples.from_helix(lims, args.input_file)


def upload_tecan_results(args):
    """Upload tecan results."""
    clarity_epp.upload.tecan.results(lims, args.process_id)


def upload_tapestation_results(args):
    """Upload tapestation results."""
    clarity_epp.upload.tapestation.results(lims, args.process_id)


def upload_bioanalyzer_results(args):
    """Upload bioanalyzer results."""
    clarity_epp.upload.bioanalyzer.results(lims, args.process_id)


# QC functions
def qc_qubit(args):
    """Set QC status based on qubit measurement."""
    clarity_epp.qc.qubit.set_qc_flag(lims, args.process_id)


def qc_fragment_length(args):
    """Set QC status based on fragment length measurement."""
    clarity_epp.qc.fragment_length.set_qc_flag(lims, args.process_id)


# Placement functions
def placement_automatic(args):
    """Copy container layout from previous step."""
    clarity_epp.placement.plate.copy_layout(lims, args.process_id)


def placement_artifact_set_sequence_name(args):
    """Change artifact name to sequence name."""
    clarity_epp.placement.artifact.set_sequence_name(lims, args.process_id)


def placement_barcode(args):
    """Check barcodes."""
    if args.type == 'check_family':
        clarity_epp.placement.barcode.check_family(lims, args.process_id)


# Generate functions
def generate_family_status(args):
    """Generate family status."""
    clarity_epp.generate.samplenames.family_status(lims, args.process_id)


if __name__ == "__main__":
    # with utils.EppLogger(main_log=config.main_log):
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers()

    output_parser = argparse.ArgumentParser(add_help=False)
    output_parser.add_argument('-o', '--output_file',  nargs='?', type=argparse.FileType('w'), default=sys.stdout, help='Output file path (default=stdout)')

    # export
    parser_export = subparser.add_parser('export', help='Export from lims.')
    subparser_export = parser_export.add_subparsers()

    parser_export_hamilton = subparser_export.add_parser('hamilton', help='Create hamilton samplesheets', parents=[output_parser])
    parser_export_hamilton.add_argument('type', choices=['filling_out', 'purify'], help='Samplesheet type')
    parser_export_hamilton.add_argument('process_id', help='Clarity lims process id')
    parser_export_hamilton.set_defaults(func=export_hamilton)

    parser_export_tecan = subparser_export.add_parser('tecan', help='Create tecan samplesheets', parents=[output_parser])
    parser_export_tecan.add_argument('process_id', help='Clarity lims process id')
    parser_export_tecan.set_defaults(func=export_tecan)

    parser_export_manual_pipetting = subparser_export.add_parser('manual', help='Create manual pipetting _exports', parents=[output_parser])
    parser_export_manual_pipetting.add_argument('type', choices=['purify', 'sequencing_pool', 'multiplex'], help='Samplesheet type')
    parser_export_manual_pipetting.add_argument('process_id', help='Clarity lims process id')
    parser_export_manual_pipetting.set_defaults(func=export_manual_pipetting)

    parser_export_caliper = subparser_export.add_parser('caliper', help='Create caliper samplesheets', parents=[output_parser])
    parser_export_caliper.add_argument('type', choices=['normalise'], help='Samplesheet type')
    parser_export_caliper.add_argument('process_id', help='Clarity lims process id')
    parser_export_caliper.set_defaults(func=export_caliper)

    parser_export_tapestation = subparser_export.add_parser('tapestation', help='Create tapestation samplesheets', parents=[output_parser])
    parser_export_tapestation.add_argument('process_id', help='Clarity lims process id')
    parser_export_tapestation.set_defaults(func=export_tapestation)

    parser_export_bioanalyzer = subparser_export.add_parser('bioanalyzer', help='Create bioanalyzer samplesheets', parents=[output_parser])
    parser_export_bioanalyzer.add_argument('process_id', help='Clarity lims process id')
    parser_export_bioanalyzer.set_defaults(func=export_bioanalyzer)

    parser_export_labels = subparser_export.add_parser('labels', help='Export container labels.', parents=[output_parser])
    parser_export_labels.add_argument('process_id', help='Clarity lims process id')
    parser_export_labels.set_defaults(func=export_labels)

    parser_export_ped = subparser_export.add_parser('ped', help='Export ped file.', parents=[output_parser])
    parser_export_ped.add_argument('process_id', help='Clarity lims process id')
    parser_export_ped.set_defaults(func=export_ped_file)

    # Sample upload
    parser_upload = subparser.add_parser('upload', help='Upload samples or results to clarity lims')
    subparser_upload = parser_upload.add_subparsers()

    parser_upload_sample = subparser_upload.add_parser('sample', help='Upload samples from helix export')
    parser_upload_sample.add_argument('input_file', type=argparse.FileType('r'), help='Input file path')
    parser_upload_sample.set_defaults(func=upload_samples)

    parser_upload_tecan = subparser_upload.add_parser('tecan', help='Upload tecan results')
    parser_upload_tecan.add_argument('process_id', help='Clarity lims process id')
    parser_upload_tecan.set_defaults(func=upload_tecan_results)

    parser_upload_tapestation = subparser_upload.add_parser('tapestation', help='Upload tapestation results')
    parser_upload_tapestation.add_argument('process_id', help='Clarity lims process id')
    parser_upload_tapestation.set_defaults(func=upload_tapestation_results)

    parser_upload_bioanalyzer = subparser_upload.add_parser('bioanalyzer', help='Upload bioanalyzer results')
    parser_upload_bioanalyzer.add_argument('process_id', help='Clarity lims process id')
    parser_upload_bioanalyzer.set_defaults(func=upload_bioanalyzer_results)

    # QC
    parser_qc = subparser.add_parser('qc', help='Set QC values/flags.')
    subparser_qc = parser_qc.add_subparsers()

    parser_qc_qubit = subparser_qc.add_parser('qubit', help='Set qubit qc flag.')
    parser_qc_qubit.add_argument('process_id', help='Clarity lims process id')
    parser_qc_qubit.set_defaults(func=qc_qubit)

    parser_qc_fragment_length = subparser_qc.add_parser('fragment_length', help='Set fragment length qc flag.')
    parser_qc_fragment_length.add_argument('process_id', help='Clarity lims process id')
    parser_qc_fragment_length.set_defaults(func=qc_fragment_length)

    # placement
    parser_placement = subparser.add_parser('placement', help='Container placement functions.')
    subparser_placement = parser_placement.add_subparsers()

    parser_placement_automatic = subparser_placement.add_parser('copy', help='Copy container layout from previous step.')
    parser_placement_automatic.add_argument('process_id', help='Clarity lims process id')
    parser_placement_automatic.set_defaults(func=placement_automatic)

    parser_placement_artifact = subparser_placement.add_parser('artifact', help='Change artifact name to sequence name.')
    parser_placement_artifact.add_argument('process_id', help='Clarity lims process id')
    parser_placement_artifact.set_defaults(func=placement_artifact_set_sequence_name)

    parser_placement_barcode = subparser_placement.add_parser('barcode_check', help='Check barcode clarity_epp.placement.')
    parser_placement_barcode.add_argument('type', choices=['check_family'], help='Check type')
    parser_placement_barcode.add_argument('process_id', help='Clarity lims process id')
    parser_placement_barcode.set_defaults(func=placement_barcode)

    # generate
    parser_generate = subparser.add_parser('generate', help='Generate samplenames functions.')
    subparser_generate = parser_generate.add_subparsers()

    parser_generate_samplenames = subparser_generate.add_parser('family_status', help='Generate family status.')
    parser_generate_samplenames.add_argument('process_id', help='Clarity lims process id')
    parser_generate_samplenames.set_defaults(func=generate_family_status)

    args = parser.parse_args()
    args.func(args)
