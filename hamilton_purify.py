"""Hamilton samplesheet epp script."""

import os

from argparse import ArgumentParser
from genologics.lims import Lims
from genologics.entities import Process
from genologics import config
from genologics.epp import EppLogger


def main(lims, process_id, output_file):
    """Create Hamilton samplesheet for purifying 96 well plate."""
    with open(output_file, 'w') as file:
        file.write('SampleID\tSample Rack barcode\tSample rack positionID\tSample Start volume\n')
        process = Process(lims, id=process_id)
        parent_process_barcode = process.parent_processes()[0].udf['Barcode plaat']
        # parent_process_barcode = process.parent_processes()[0].output_containers()[0].name
        sample_info = {}
        wells = (
            'A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'A3', 'B3', 'C3', 'D3', 'E3', 'F3', 'G3',
            'H3', 'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4', 'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5', 'H5', 'A6', 'B6', 'C6', 'D6', 'E6', 'F6',
            'G6', 'H6', 'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7', 'A8', 'B8', 'C8', 'D8', 'E8', 'F8', 'G8', 'H8', 'A9', 'B9', 'C9', 'D9', 'E9',
            'F9', 'G9', 'H9', 'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10', 'H10', 'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11', 'A12',
            'B12', 'C12', 'D12', 'E12', 'F12', 'G12', 'H12'
        )
        for placement, artifact in process.output_containers()[0].placements.iteritems():
            placement = ''.join(placement.split(':'))
            sample_info[placement] = [artifact.samples[0].udf['Dx Fractienummer'], parent_process_barcode, placement, '50']

        for i in range(0, 96):
            if sample_info.has_key(wells[i]):
                file.write('{0}\t{1}\t{2}\t{3}\n'.format(
                    sample_info[wells[i]][0],
                    sample_info[wells[i]][1],
                    sample_info[wells[i]][2],
                    sample_info[wells[i]][3]
                    ))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("process_id", help="Process id")
    parser.add_argument("output_file", help="Output file name")

    args = parser.parse_args()
    config_file = "{path}/{config_file}".format(
        path=os.path.realpath(os.path.dirname(__file__)),
        config_file='genologics.conf'
    )
    BASEURI, USERNAME, PASSWORD, VERSION, MAIN_LOG = config.load_config(specified_config=config_file)

    with EppLogger():
        lims = Lims(BASEURI, USERNAME, PASSWORD)
        main(lims, args.process_id, args.output_file)
