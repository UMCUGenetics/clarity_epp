"""Utilities related to Process.

A process is defined as a lab procedure that has been configured and included as part of a protocol.
The Clarity LIMS terminology equivalent is 'Step'. All steps have a master step as their foundation.
"""

from s4.clarity.artifact import Artifact
from s4.clarity.process import Process


def get_well_plate_from_process(process: Process) -> dict[str, Artifact]:
    """Get well plate artifacts for a given process.

    Args:
        process: Clarity process object.

    Returns:
        Dictionary with well positions as keys and Artifacts as values.

    """
    well_plate = get_artifact_containers_from_process(process, format_placement_to_position=True)
    if len(well_plate) != 1:
        raise ValueError(f"Expected one container, but found {len(well_plate)} containers in process {process.limsid}.")
    return well_plate.values()


def get_artifact_containers_from_process(
    process: Process, format_placement_to_position: bool = False
) -> dict[str, dict[str, Artifact]]:
    """Get containers from artifacts in a given process.

    Args:
        process: Clarity process object.
        format_placement_to_position: Format placement to well  well position "A1" (True) or keep original placement format
        "A:1" (False).

    Returns:
        Dictionary with container IDs as keys and dictionaries of container positions and Artifact objects as values.
    """
    artifact_containers = {}
    for artifact in process.outputs:
        container_id = artifact.container.limsid
        if container_id not in artifact_containers:
            artifact_containers[container_id] = {}

        if format_placement_to_position:
            placement = "".join(artifact.location_value.split(":"))
        else:
            placement = artifact.location_value

        artifact_containers[container_id][placement] = artifact

    return artifact_containers
