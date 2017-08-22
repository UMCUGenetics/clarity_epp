#!venv/bin/python
"""Clarity epp application."""

import argparse

from genologics.lims import Lims

import config
# import utils
import samplesheet

# Setup lims connection
lims = Lims(config.baseuri, config.username, config.password)


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


if __name__ == "__main__":
    # with utils.EppLogger(main_log=config.main_log):
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers()

    # samplesheet
    parser_samplesheet = subparser.add_parser('samplesheet', help='Create samplsheets')
    subparser_samplesheet = parser_samplesheet.add_subparsers()

    parser_hamilton = subparser_samplesheet.add_parser('hamilton', help='Create hamilton samplsheets')
    parser_hamilton.add_argument('type', choices=['filling_out', 'purify'], help='Samplesheet type')
    parser_hamilton.add_argument('process_id', help='Clarity lims process id')
    parser_hamilton.add_argument('output_file', help='/path/to/output_file')
    parser_hamilton.set_defaults(func=hamilton)

    parser_tecan = subparser_samplesheet.add_parser('tecan', help='Create tecan samplsheets')
    parser_tecan.add_argument('process_id', help='Clarity lims process id')
    parser_tecan.add_argument('output_file', help='/path/to/output_file')
    parser_tecan.set_defaults(func=tecan)

    parser_manual_pipetting = subparser_samplesheet.add_parser('manual', help='Create manual pipetting samplesheets')
    parser_manual_pipetting.add_argument('type', choices=['purify'], help='Samplesheet type')
    parser_manual_pipetting.add_argument('process_id', help='Clarity lims process id')
    parser_manual_pipetting.add_argument('output_file', help='/path/to/output_file')
    parser_manual_pipetting.set_defaults(func=manual_pipetting)

    args = parser.parse_args()
    args.func(args)
