"""Hamilton samplesheet epp script."""

from argparse import ArgumentParser
from genologics.lims import Lims
from genologics.entities import Process
from genologics.config import BASEURI, USERNAME, PASSWORD
from genologics.epp import EppLogger


def main(lims, process_id, output_file):
    """Create Hamilton samplesheet for filling out 96 well plate."""
    with open(output_file, 'w') as file:
        process = Process(lims, id=process_id)
        for placement, artifact in process.output_containers()[0].placements.iteritems():
            file.write('{0}\t{1}\n'.format(placement, artifact.name))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("process_id", help="Process id")
    parser.add_argument("output_file", help="Output file name")

    args = parser.parse_args()

    with EppLogger():
        lims = Lims(BASEURI, USERNAME, PASSWORD)
        lims.check_version()
        main(lims, args.process_id, args.output_file)
