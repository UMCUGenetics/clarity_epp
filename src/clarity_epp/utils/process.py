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
    well_plate = {}

    for artifact in process.outputs:
        placement = "".join(artifact.location_value.split(":"))
        well_plate[placement] = artifact

    return well_plate


def sort_process_artifacts_on_container_limsid(process_outputs: list, reverse: bool = True) -> list:
    """Sort process outputs (artifacts) by using the artifacts container lims ID.

    Args:
        process_outputs: List of artifacts, often in this case of type Analyte and represents a derived sample.
        reverse (optional): Whether sort order should be reversed. Defaults to True.

    Returns:
        Sorted artifacts.
    """
    return sorted(process_outputs, key=lambda artifact: artifact.container.limsid, reverse=reverse)
