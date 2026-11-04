"""Action to export labels."""

from typing import Annotated

import typer
from s4.clarity.artifact import Artifact

from clarity_epp.core.templates import render_template
from clarity_epp.services.clarity import ClarityFactory
from clarity_epp.utils.process import get_artifact_containers_from_process

cli = typer.Typer(no_args_is_help=True)


def get_artifact_container_labels(
    artifact_containers: dict[str, dict[str, Artifact]],
    description: str | None,
) -> list[dict[str, str]]:
    """Get container artifact labels for given containers.

    Args:
        artifact_containers: Dictionary with container IDs as keys and dictionaries of container positions and Artifact objects as values.
        description: Custom description to include in the output. Defaults to None.
        placements_to_keep: List of well placements to include in the output.

    Returns:
        List of dictionaries with artifact name, container name, and description.
    """
    descriptions = description.split(",") if description and "," in description else None

    artifact_container_labels = []
    list_artifact_container_ids = list(artifact_containers)
    for index, container_id in enumerate(sorted(list_artifact_container_ids, reverse=True)):
        for artifact in artifact_containers[container_id].values():
            artifact_container_labels.append(
                {
                    "artifact_name": artifact.name,
                    "container_name": artifact.container.name,
                    "description": (descriptions[index] if descriptions else description),
                }
            )
    return artifact_container_labels


@cli.command()
def export_labels_container(
    process_id: str,
    with_artifacts: bool = False,
    description: str | None = None,
    output_file: Annotated[typer.FileTextWrite, typer.Argument()] = "/dev/stdout",
):
    """Export container labels using predefined templates.

    Args:
        process_id: Clarity's Process ID to use
        with_artifacts (optional): Whether output should include linked artifact labels. Defaults to False.
        description (optional): Custom description to include in the output. Defaults to None.
        output_file (optional): Output file location to send rendered output to. Defaults to "/dev/stdout".
    """
    clarity = ClarityFactory.get_instance()
    process = clarity.processes.from_limsid(process_id)

    artifact_placement_container = get_artifact_containers_from_process(process, format_placement_to_position=True)
    artifact_container_labels = get_artifact_container_labels(artifact_placement_container, description)

    if with_artifacts:
        template_to_use = "instruments/label_printer_container_sample.tsv"
    else:
        template_to_use = "instruments/label_printer_container.tsv"

    output_file.write(
        render_template(
            template_to_use,
            artifacts=artifact_container_labels,
            include_description=bool(description),
        )
    )
