"""Caliper export functions."""
import string
from typing import TextIO, Dict, Tuple

from genologics.entities import Process

from clarity_epp.export.utils import plate96_wells, nm_from_ng_ul, location_to_well

def write_samplesheet(
    output_file: TextIO,
    plate_id_input: str,
    plate_id_output: str,
    rows_by_well: Dict[str, Tuple[str, float, float]],) -> None:
    """
    Write Caliper samplesheet.
    Args:
        output_file: Output file to write to.
        plate_id_input: Input plate ID.
        plate_id_output: Output plate ID.
        rows_by_well: Dictionary mapping well numbers to row numbers.
    """
    output_file.write('Monsternummer\tPlate_Id_input\tWell\tPlate_Id_output\tPipetteervolume DNA (ul)\tPipetteervolume H2O (ul)\n')
    for well in plate96_wells():
        if well in rows_by_well:
            name, vol_dna, vol_h2o = rows_by_well[well]
        else:
            name, vol_dna, vol_h2o = "Leeg", 0.0, 0.0
        output_file.write(
            f"{name}\t{plate_id_input}\t{well}\t{plate_id_output}\t{vol_dna:.1f}\t{vol_h2o:.1f}\n"
        )


def samplesheet_dilute(lims, process_id: str, output_file: TextIO) -> None:
    """
    Create a samplesheet with diluted plates and write it to file.
    Args:
        lims:
        process_id: Process ID.
        output_file: Output file.
    """
    process = Process(lims, id=process_id)

    output = {}  # save output data to dict, to be able to sort on well.
    nM_pool = process.udf['Dx Pool verdunning (nM)']
    output_ul = process.udf['Eindvolume (ul)']

    # Get input and output plate id from 1 sample, input plate is the same for all samples.
    input_artifacts = process.all_inputs()
    first_artifact = input_artifacts[0]
    plate_id_input = first_artifact.location[0].name
    plate_id_output = process.outputs_per_input(first_artifact.id, Analyte=True)[0].location[0].name

    rows_by_well: Dict[str, Tuple[str, float, float]] = {}

    for artifact in input_artifacts:
        size_bp = float(artifact.udf['Dx Fragmentlengte (bp)'])
        conc_ng_ul = float(artifact.udf['Dx Concentratie fluorescentie (ng/ul)'])

        nM_dna = nm_from_ng_ul(conc_ng_ul, size_bp)
        ul_sample = (nM_pool / nM_dna) * output_ul
        ul_water = output_ul - ul_sample

        well = location_to_well(artifact.location[1])
        rows_by_well[well] = (artifact.name, float(ul_sample), float(ul_water))

    write_samplesheet(output_file, plate_id_input, plate_id_output, rows_by_well)
