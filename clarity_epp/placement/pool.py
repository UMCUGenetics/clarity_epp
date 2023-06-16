"""Pool  placement functions."""

from genologics.entities import Process, Workflow, Step

from .. import get_sequence_name, get_sample_artifacts_from_pool
import config


def unpooling(lims, process_id):
    """Unpool samples after sequencing."""
    process = Process(lims, id=process_id)

    if process.step.actions.next_actions[0]['action'] == 'complete':  # Only unpool complete sequencing runs.
        pool_artifact = process.all_inputs()[0]
        pool_artifact_parent_process = pool_artifact.parent_process

        run_id = pool_artifact.name  # Assume run id is set as pool name using placement/artifact/set_runid_name
        sample_artifacts = []  # sample artifacts before pooling
        sample_projects = {}

        # Get sample projects from samplesheet
        for artifact in pool_artifact_parent_process.result_files():
            if (artifact.name == 'SampleSheet csv' or artifact.name == 'Sample Sheet') and artifact.files:
                file_id = artifact.files[0].id
                sample_sheet = lims.get_file_contents(id=file_id)
                project_index = None
                sample_index = None
                for line in sample_sheet.split('\n'):
                    data = line.rstrip().split(',')

                    if 'Sample_Project' in data and 'Sample_ID' in data:
                        project_index = data.index('Sample_Project')
                        sample_index = data.index('Sample_ID')
                    elif project_index and len(data) >= project_index:
                        sample_projects[data[sample_index]] = data[project_index]

        # Parse sequencing run samples and move Dx samples to post sequencing workflow
        for sample_artifact in get_sample_artifacts_from_pool(lims, pool_artifact):
            sample = sample_artifact.samples[0]   # Asume all samples metadata is identical.

            # Set sample sequencing run and project
            sample_artifact.udf['Dx Sequencing Run ID'] = run_id
            # Use sample.name for external (clarity_portal) samples
            if 'Sample Type' in sample.udf and 'library' in sample.udf['Sample Type']:
                sample_artifact.udf['Dx Sequencing Run Project'] = sample_projects[sample.name]
            else:  # Use sample_artifact.name for Dx samples (upload via Helix)
                sample_artifact.udf['Dx Sequencing Run Project'] = sample_projects[sample_artifact.name]
            sample_artifact.put()

            # Only move DX production samples to post sequencing workflow
            if sample.project and sample.project.udf['Application'] == 'DX':
                sample_artifacts.append(sample_artifact)

        lims.route_artifacts(sample_artifacts, workflow_uri=Workflow(lims, id=config.post_sequencing_workflow).uri)


def create_patient_pools(lims, process_id):
    """Create patient pools for Dx samples based on UDF 'Dx Persoons ID'."""
    step = Step(lims, id=process_id)
    step_pools = step.step_pools
    patient_pools = {}

    # Create patient pools
    for artifact in step_pools.available_inputs:
        sample = artifact.samples[0]  # Assume one sample per artifact
        if sample.udf['Dx Persoons ID'] not in patient_pools:
            patient_pools[sample.udf['Dx Persoons ID']] = {
                'name': str(sample.udf['Dx Persoons ID']),
                'inputs': []
            }
        patient_pools[sample.udf['Dx Persoons ID']]['inputs'].append(artifact)

    # Transform patient pools to list and put to clarity
    step_pools.set_pools(list(patient_pools.values()))
    step_pools.put()

    # Rename pools to sequence name
    process = Process(lims, id=process_id)
    for artifact in process.all_outputs():
        artifact.name = get_sequence_name(artifact)
        artifact.put()
