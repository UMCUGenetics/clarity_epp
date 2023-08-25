"""Artifact placement functions."""

from genologics.entities import Process, Workflow

from .. import get_sequence_name
import config


def set_sequence_name(lims, process_id):
    """Change artifact name to sequnece name."""
    process = Process(lims, id=process_id)
    for artifact in process.analytes()[0]:
        artifact.name = get_sequence_name(artifact)
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


def route_to_workflow(lims, process_id, workflow):
    """Route artifacts to a workflow."""
    process = Process(lims, id=process_id)

    # Get all artifacts with workflow status == completed.
    artifacts_completed = [
        action_artifact['artifact'] for action_artifact in process.step.actions.get_next_actions()
        if action_artifact['action'] == 'complete'
    ]

    if workflow == 'post_bioinf':
        #  Remove research artifacts
        route_artifacts = [
            artifact for artifact in artifacts_completed
            if artifact.samples[0].udf['Dx Stoftest code'] != config.stoftestcode_research  # Asume all samples metadata is identical.
        ]
        lims.route_artifacts(route_artifacts, workflow_uri=Workflow(lims, id=config.post_bioinf_workflow).uri)

    elif workflow == 'sequencing':
        lims.route_artifacts(artifacts_completed, workflow_uri=Workflow(lims, id=config.sequencing_workflow).uri)


def set_norm_manual_udf(lims, process_id):
    """Combine mix sample udfs 'Dx norm. manueel'."""
    process = Process(lims, id=process_id)

    for artifact in process.all_outputs():
        artifact.udf['Dx norm. manueel'] = False
        for sample in artifact.samples:
            if sample.udf['Dx norm. manueel'] == True:
                artifact.udf['Dx norm. manueel'] = True
        artifact.put()