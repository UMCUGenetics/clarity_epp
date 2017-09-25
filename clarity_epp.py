#!venv/bin/python
"""Clarity epp application."""

import sys
import argparse

from genologics.lims import Lims

import config
import samplesheet
import upload

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


# Sample Upload
def upload_samples(args):
    """Upload samples from helix output file."""
    upload.samples.from_helix(lims, args.input_file)


if __name__ == "__main__":
    # with utils.EppLogger(main_log=config.main_log):
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers()

    output_parser = argparse.ArgumentParser(add_help=False)
    output_parser.add_argument('-o', '--output_file',  nargs='?', type=argparse.FileType('w'), default=sys.stdout, help='Output file path (default=stdout)')

    # samplesheet
    parser_samplesheet = subparser.add_parser('samplesheet', help='Create samplesheets')
    subparser_samplesheet = parser_samplesheet.add_subparsers()

    parser_hamilton = subparser_samplesheet.add_parser('hamilton', help='Create hamilton samplesheets', parents=[output_parser])
    parser_hamilton.add_argument('type', choices=['filling_out', 'purify'], help='Samplesheet type')
    parser_hamilton.add_argument('process_id', help='Clarity lims process id')

    parser_hamilton.set_defaults(func=hamilton)

    parser_tecan = subparser_samplesheet.add_parser('tecan', help='Create tecan samplesheets', parents=[output_parser])
    parser_tecan.add_argument('process_id', help='Clarity lims process id')
    parser_tecan.set_defaults(func=tecan)

    parser_manual_pipetting = subparser_samplesheet.add_parser('manual', help='Create manual pipetting samplesheets', parents=[output_parser])
    parser_manual_pipetting.add_argument('type', choices=['purify'], help='Samplesheet type')
    parser_manual_pipetting.add_argument('process_id', help='Clarity lims process id')
    parser_manual_pipetting.set_defaults(func=manual_pipetting)

    parser_caliper = subparser_samplesheet.add_parser('caliper', help='Create caliper samplesheets', parents=[output_parser])
    parser_caliper.add_argument('type', choices=['normalise'], help='Samplesheet type')
    parser_caliper.add_argument('process_id', help='Clarity lims process id')
    parser_caliper.set_defaults(func=caliper)

    # Sample upload
    parser_sample_upload = subparser.add_parser('sample_upload', help='Upload samples from helix export')
    parser_sample_upload.add_argument('input_file', type=argparse.FileType('r'), help='Input file path')
    parser_sample_upload.set_defaults(func=upload_samples)

    args = parser.parse_args()
    args.func(args)
