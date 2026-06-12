from s4.clarity.artifact import Artifact
from s4.clarity.process import Process


def get_well_plate_from_process(process: Process) -> dict[str, Artifact]:
    """Get well plate artifacts for a given process.

    Args:
        process: Clarity process object.

    Returns:
        Dictionary with well positions as keys and Artifacts as values.

    """
    well_plate = {}

    for artifact in process.outputs:
        placement = "".join(artifact.location_value.split(":"))
        well_plate[placement] = artifact

    return well_plate
