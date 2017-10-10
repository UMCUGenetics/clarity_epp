#!venv/bin/python
"""Clarity epp application."""

import sys
import argparse

from genologics.lims import Lims

import config
import samplesheet
import upload
import qc
import placement

# Setup lims connection
lims = Lims(config.baseuri, config.username, config.password)


# Samplesheets
def hamilton(args):
    """Create samplesheets for hamilton machine."""
    if args.type == 'filling_out':
        samplesheet.hamilton.filling_out(lims, args.process_id, args.output_file)
    elif args.type == 'purify':
        samplesheet.hamilton.purify(lims, args.process_id, args.output_file)


def manual_pipetting(args):
    """Create samplesheets for manual pipetting."""
    if args.type == 'purify':
        samplesheet.manual_pipetting.purify(lims, args.process_id, args.output_file)


def tecan(args):
    """Create samplesheets for tecan machine."""
    samplesheet.tecan.run_tecan(lims, args.process_id, args.output_file)


def caliper(args):
    """Create samplesheets for caliper machine."""
    if args.type == 'normalise':
        samplesheet.caliper.normalise(lims, args.process_id, args.output_file)


def tapestation(args):
    """Create samplesheets for Tapestation machine."""
    samplesheet.tapestation.run_tapestation(lims, args.process_id, args.output_file)


# Sample Upload
def upload_samples(args):
    """Upload samples from helix output file."""
    upload.samples.from_helix(lims, args.input_file)


def upload_tecan_results(args):
    """Upload tecan results."""
    upload.tecan.results(lims, args.process_id)


# QC functions
def qc_qubit(args):
    """Set QC status based on qubit measurement."""
    qc.qubit.set_qc_flag(lims, args.process_id)


# Placement functions
def placement_automatic(args):
    """Copy container layout from previous step."""
    placement.plate.copy_layout(lims, args.process_id)


if __name__ == "__main__":
    # with utils.EppLogger(main_log=config.main_log):
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers()

    output_parser = argparse.ArgumentParser(add_help=False)
    output_parser.add_argument('-o', '--output_file',  nargs='?', type=argparse.FileType('w'), default=sys.stdout, help='Output file path (default=stdout)')

    # samplesheet
    parser_samplesheet = subparser.add_parser('samplesheet', help='Create samplesheets')
    subparser_samplesheet = parser_samplesheet.add_subparsers()

    parser_samplesheet_hamilton = subparser_samplesheet.add_parser('hamilton', help='Create hamilton samplesheets', parents=[output_parser])
    parser_samplesheet_hamilton.add_argument('type', choices=['filling_out', 'purify'], help='Samplesheet type')
    parser_samplesheet_hamilton.add_argument('process_id', help='Clarity lims process id')
    parser_samplesheet_hamilton.set_defaults(func=hamilton)

    parser_samplesheet_tecan = subparser_samplesheet.add_parser('tecan', help='Create tecan samplesheets', parents=[output_parser])
    parser_samplesheet_tecan.add_argument('process_id', help='Clarity lims process id')
    parser_samplesheet_tecan.set_defaults(func=tecan)

    parser_samplesheet_manual_pipetting = subparser_samplesheet.add_parser('manual', help='Create manual pipetting samplesheets', parents=[output_parser])
    parser_samplesheet_manual_pipetting.add_argument('type', choices=['purify'], help='Samplesheet type')
    parser_samplesheet_manual_pipetting.add_argument('process_id', help='Clarity lims process id')
    parser_samplesheet_manual_pipetting.set_defaults(func=manual_pipetting)

    parser_samplesheet_caliper = subparser_samplesheet.add_parser('caliper', help='Create caliper samplesheets', parents=[output_parser])
    parser_samplesheet_caliper.add_argument('type', choices=['normalise'], help='Samplesheet type')
    parser_samplesheet_caliper.add_argument('process_id', help='Clarity lims process id')
    parser_samplesheet_caliper.set_defaults(func=caliper)

    parser_samplesheet_tapestation = subparser_samplesheet.add_parser('tapestation', help='Create tapestation samplesheets', parents=[output_parser])
    parser_samplesheet_tapestation.add_argument('process_id', help='Clarity lims process id')
    parser_samplesheet_tapestation.set_defaults(func=tapestation)

    # Sample upload
    parser_upload = subparser.add_parser('upload', help='Upload samples or results to clarity lims')
    subparser_upload = parser_upload.add_subparsers()

    parser_upload_sample = subparser_upload.add_parser('sample', help='Upload samples from helix export')
    parser_upload_sample.add_argument('input_file', type=argparse.FileType('r'), help='Input file path')
    parser_upload_sample.set_defaults(func=upload_samples)

    parser_upload_tecan = subparser_upload.add_parser('tecan', help='Upload tecan results')
    parser_upload_tecan.add_argument('process_id', help='Clarity lims process id')
    parser_upload_tecan.set_defaults(func=upload_tecan_results)

    # QC
    parser_qc = subparser.add_parser('qc', help='Set QC values/flags.')
    subparser_qc = parser_qc.add_subparsers()

    parser_qc_qubit = subparser_qc.add_parser('qubit', help='Set qubit qc flag.')
    parser_qc_qubit.add_argument('process_id', help='Clarity lims process id')
    parser_qc_qubit.set_defaults(func=qc_qubit)

    # placement
    parser_placement = subparser.add_parser('placement', help='Container placement functions.')
    subparser_placement = parser_placement.add_subparsers()

    parser_placement_automatic = subparser_placement.add_parser('copy', help='Copy container layout from previous step.')
    parser_placement_automatic.add_argument('process_id', help='Clarity lims process id')
    parser_placement_automatic.set_defaults(func=placement_automatic)

    args = parser.parse_args()
    args.func(args)
