"""Clarity epp application."""

import argparse
import os

from genologics.lims import Lims
from genologics import config
from genologics.epp import EppLogger

import samplesheet

# Setup lims connection
config_file = "{path}/{config_file}".format(
    path=os.path.realpath(os.path.dirname(__file__)),
    config_file='genologics.conf'
)
BASEURI, USERNAME, PASSWORD, VERSION, MAIN_LOG = config.load_config(specified_config=config_file)
lims = Lims(BASEURI, USERNAME, PASSWORD)


def hamilton(args):
    """Create samplesheets for hamilton machine."""
    if args.type == 'filling_out':
        samplesheet.hamilton.filling_out(lims, args.process_id, args.output_file)
    elif args.type == 'purify':
        samplesheet.hamilton.purify(lims, args.process_id, args.output_file)


if __name__ == "__main__":
    with EppLogger():
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
