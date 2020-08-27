"""Artifact placement functions."""

from genologics.entities import Process, Workflow

from .. import get_sequence_name
import config


def set_sequence_name(lims, process_id):
    """Change artifact name to sequnece name."""
    process = Process(lims, id=process_id)
    for artifact in process.analytes()[0]:
        sample = artifact.samples[0]
        artifact.name = get_sequence_name(sample)
        artifact.put()


def set_runid_name(lims, process_id):
    """Change artifact name to run id."""
    process = Process(lims, id=process_id)
    analyte = process.analytes()[0][0]
    input_artifact = process.all_inputs()[0]

    container_name = analyte.container.name

    # Find sequencing process
    # Assume one sequence process per input artifact
    for sequence_process_type in config.sequence_process_types:
        sequence_processes = lims.get_processes(type=sequence_process_type, inputartifactlimsid=input_artifact.id)
        for sequence_process in sequence_processes:
            if sequence_process.analytes()[0][0].container.name == container_name:
                analyte.name = sequence_process.udf['Run ID']
                analyte.put()


def route_to_workflow(lims, process_id):
    """Route artifacts to a workflow."""
    process = Process(lims, id=process_id)
    route_artifacts = []

    for action_artifact in process.step.actions.get_next_actions():
        artifact = action_artifact['artifact']
        action = action_artifact['action']
        if action == 'complete' and artifact.samples[0].udf['Dx Stoftest code'] != config.research_stoftest_code:
            route_artifacts.append(artifact)

    lims.route_artifacts(route_artifacts, workflow_uri=Workflow(lims, id=config.post_bioinf_workflow).uri)
