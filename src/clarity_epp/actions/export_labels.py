"""Action to export labels."""

from typing import Annotated

import typer

from clarity_epp.core.templates import render_template
from clarity_epp.services.clarity import ClarityFactory
from clarity_epp.utils.process import sort_process_artifacts_on_container_limsid

cli = typer.Typer(no_args_is_help=True)


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
    descriptions = description.split(",") if description and "," in description else None

    clarity = ClarityFactory.get_instance()
    process = clarity.processes.from_limsid(process_id)
    sorted_artifacts = sort_process_artifacts_on_container_limsid(process.outputs)

    artifacts_container = [
        {
            "artifact_name": artifact.name,
            "container_name": artifact.container.name,
            "description": (descriptions[index] if descriptions else description),
        }
        for index, artifact in enumerate(sorted_artifacts)
    ]

    if with_artifacts:
        template_to_use = "actions/labels_container.tsv"
    else:
        template_to_use = "actions/labels_container_sample.tsv"

    output_file.write(
        render_template(
            template_to_use,
            artifacts=artifacts_container,
            include_description=bool(description),
        )
    )
