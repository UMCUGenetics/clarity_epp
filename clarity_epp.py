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

    args = parser.parse_args()
    args.func(args)
