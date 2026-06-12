import typer
from typing_extensions import Annotated

from clarity_epp.core.templates import render_template
from clarity_epp.services.clarity import ClarityFactory
from clarity_epp.utils.container import sort_96_well_plate
from clarity_epp.utils.process import get_well_plate_from_process

cli = typer.Typer(no_args_is_help=True)


@cli.command()
def export_qc_samplesheet(
    process_id: str, output_file: Annotated[typer.FileTextWrite, typer.Argument()] = "/dev/stdout"
) -> None:
    """
    Export QC samplesheet.

    Args:
        process_id: Clarity process id.
        output_file: Output file. Defaults to "/dev/stdout".
    """
    clarity = ClarityFactory.get_instance()

    process = clarity.processes.from_limsid(process_id)
    well_plate = get_well_plate_from_process(process)
    well_artifact = []

    for well in sort_96_well_plate(well_plate.keys()):
        # Set correct artifact name
        artifact = well_plate[well]
        if len(artifact.samples) == 1:
            artifact_name = artifact.name.split("_")[0]
        else:
            artifact_name = artifact.name
        well_artifact.append((well, artifact_name))

    output_file.write(render_template("instruments/tecan_qc_samplesheet.tsv", wells=well_artifact))
