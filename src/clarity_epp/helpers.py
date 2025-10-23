from genologics.entities import Artifact, Process


def get_well_plate_from_process(process: Process) -> dict[str, Artifact]:
    """Get well plate artifacts for a given process.

    Args:
        process (Process): Clarity process object.

    Returns:
        dict[str, Artifact]: Dictionary with well positions as keys and Artifacts as values.

    """
    well_plate = {}
    for placement, artifact in process.output_containers()[0].placements.items():
        placement = "".join(placement.split(":"))
        well_plate[placement] = artifact

    return well_plate
