"""Artifact placement functions."""

from genologics.entities import Process, Workflow

import config
from clarity_epp.export.utils import sort_artifact_list

from .. import get_sample_artifacts_from_pool, get_sequence_name


def set_sequence_name(lims, process_id):
    """Change artifact name to sequnece name."""
    process = Process(lims, id=process_id)
    for artifact in process.analytes()[0]:
        artifact.name = get_sequence_name(artifact)
        artifact.put()


def set_runid_name(lims, process_id):
    """Change artifact name to run id."""
    process = Process(lims, id=process_id)
    input_artifact = process.all_inputs()[0]

    # Fix for NovaSeqXPlus workflow configuration
    # TODO: Set NovaSeqXPlus step to 'Analysis' type.
    if 'NovaSeqXPlus' in input_artifact.parent_process.type.name:
        input_artifact = input_artifact.parent_process.all_inputs()[0]

    # Find sequencing process
    # Assume one sequence process per input artifact
    for sequence_process_type in config.sequence_process_types:
        sequence_processes = lims.get_processes(type=sequence_process_type, inputartifactlimsid=input_artifact.id)
        for sequence_process in sequence_processes:
            sequence_process_lanes = sorted(sequence_process.analytes()[0], key=sort_artifact_list)
            for lane_idx, lane in enumerate(sorted(process.analytes()[0], key=sort_artifact_list)):
                if sequence_process_lanes[lane_idx].container.name == lane.container.name:
                    lane.name = sequence_process.udf['Run ID']
                    lane.put()


def route_to_workflow(lims, process_id, workflow):
    """Route artifacts to a workflow."""
    process = Process(lims, id=process_id)

    # Get all artifacts with workflow status == completed.
    artifacts_completed = [
        action_artifact['artifact'] for action_artifact in process.step.actions.get_next_actions()
        if action_artifact['action'] == 'complete'
    ]

    if workflow == 'post_bioinf':
        #  Select WES artifacts
        route_artifacts_wes = [
            artifact for artifact in artifacts_completed
            # Asume all samples metadata is identical.
            if artifact.samples[0].udf['Dx Stoftest code'] == config.stoftestcode_wes
            or artifact.samples[0].udf['Dx Stoftest code'] == config.stoftestcode_wes_duplo
        ]

        #  Select srWGS artifacts
        route_artifacts_srwgs = [
            artifact for artifact in artifacts_completed
            # Asume all samples metadata is identical.
            if artifact.samples[0].udf['Dx Stoftest code'] == config.stoftestcode_srwgs
            or artifact.samples[0].udf['Dx Stoftest code'] == config.stoftestcode_srwgs_duplo
        ]

        if route_artifacts_wes:
            lims.route_artifacts(route_artifacts_wes, workflow_uri=Workflow(lims, id=config.post_bioinf_workflow_wes).uri)
        if route_artifacts_srwgs:
            lims.route_artifacts(route_artifacts_srwgs, workflow_uri=Workflow(lims, id=config.post_bioinf_workflow_srwgs).uri)

    elif workflow == 'sequencing':
        lims.route_artifacts(artifacts_completed, workflow_uri=Workflow(lims, id=config.sequencing_workflow).uri)


def set_norm_manual_udf(lims, process_id):
    """Combine mix sample udfs 'Dx norm. manueel'."""
    process = Process(lims, id=process_id)

    for artifact in process.all_outputs():
        artifact.udf['Dx norm. manueel'] = False
        for sample in artifact.samples:
            if sample.udf['Dx norm. manueel']:
                artifact.udf['Dx norm. manueel'] = True
        artifact.put()


def set_udf_lpsrwgs_pool(lims, process_id):
    """Only for all LPsrWGS artifacts in the output pools; fills the udf 'Dx LPpool' of corresponding srWGS output artifacts of
    'Dx sample duplicate' step with the output pool name

    Args:
        lims (object): Lims connection
        process (object): Lims Process object
    """
    process = Process(lims, id=process_id)
    analytes = process.analytes()[0]
    for pool in analytes:
        for pool_sample_artifact in get_sample_artifacts_from_pool(lims, pool):
            if pool_sample_artifact.name.split('_')[-1] == 'LPsrWGS':
                duplicate_process = pool_sample_artifact.parent_process.parent_processes()[0]
                for duplicate_output_artifact in duplicate_process.analytes()[0]:
                    if (pool_sample_artifact.name.split('_')[0] == duplicate_output_artifact.name.split('_')[0]
                        and duplicate_output_artifact.name.split('_')[-1] == 'srWGS'):
                        pool_sample_artifact.udf['Dx LPpool'] = pool.name
                        pool_sample_artifact.put()
