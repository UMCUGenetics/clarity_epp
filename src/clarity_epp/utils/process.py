from core.config import settings

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

def get_step_url_from_process_id(process_id: str) -> str:
    """
    Get clarity 'work-complete' URL for step.

    Args:
        process_id: Clarity process id.

    Returns:
        str: URL of step
    """
    step_id = process_id.split("-")[1]
    clarity_url = f"{settings.clarity.base_url}/clarity"
    return f"{clarity_url}/work-complete/{step_id}"