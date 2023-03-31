"""Artifact placement functions."""

from genologics.entities import Process, Workflow

from .. import convert_location
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


def route_to_workflow(lims, process_id, workflow):
    """Route artifacts to a workflow."""
    process = Process(lims, id=process_id)

    # Get all artifacts with workflow status == completed.
    artifacts_completed = [
        action_artifact['artifact'] for action_artifact in process.step.actions.get_next_actions()
        if action_artifact['action'] == 'complete'
    ]

    if workflow == 'post_bioinf':
        stoftest_artifacts = {}
        for artifact in artifacts_completed:
            sample = artifact.samples[0]  # Asume 1 sample per artifact

            # Add stoftest to dict
            if sample.udf['Dx Stoftest code'] not in stoftest_artifacts:
                stoftest_artifacts[sample.udf['Dx Stoftest code']] = {'single': [], 'trio': []}

            # Remove research artifacts
            if sample.udf['Dx Stoftest code'] != config.stoftestcode_research:
                # Find trio
                if(
                    sample.udf['Dx Familie status'] == 'Ouder'
                    or ('Dx Gerelateerde onderzoeken' in sample.udf and sample.udf['Dx Gerelateerde onderzoeken'])
                ):
                    stoftest_artifacts[sample.udf['Dx Stoftest code']]['trio'].append(artifact)
                else:
                    stoftest_artifacts[sample.udf['Dx Stoftest code']]['single'].append(artifact)

        for stoftest, route_artifacts in stoftest_artifacts.items():
            if route_artifacts['single']:
                workflow = Workflow(lims, id=config.post_bioinf_workflow[stoftest]['single']['workflow'])
                stage = workflow.stages[config.post_bioinf_workflow[stoftest]['single']['stage']]
                lims.route_artifacts(route_artifacts['single'], workflow_uri=workflow.uri, stage_uri=stage.uri)

            if route_artifacts['trio']:
                workflow = Workflow(lims, id=config.post_bioinf_workflow[stoftest]['trio']['workflow'])
                stage = workflow.stages[config.post_bioinf_workflow[stoftest]['trio']['stage']]
                lims.route_artifacts(route_artifacts['trio'], workflow_uri=workflow.uri, stage_uri=stage.uri)

    elif workflow == 'sequencing':
        lims.route_artifacts(artifacts_completed, workflow_uri=Workflow(lims, id=config.sequencing_workflow).uri)


def set_sample_name_array(lims, process_id):
    """Change artifact name to containername_number."""
    process = Process(lims, id=process_id)
    for artifact in process.all_outputs():
        output_container = artifact.location[0].name
        output_well = ''.join(artifact.location[1].split(':'))
        converted_location = convert_location(output_well)
        artifact.name = ('{container_name}_{location}').format(container_name=output_container, location=converted_location)
        artifact.put()