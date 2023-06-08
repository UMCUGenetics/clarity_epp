"""Pool  placement functions."""

from genologics.entities import Artifact, Process, Workflow, Step

from .. import get_sequence_name
import config


def unpooling(lims, process_id):
    """Unpool samples after sequencing."""
    process = Process(lims, id=process_id)

    if process.step.actions.next_actions[0]['action'] == 'complete':  # Only unpool complete sequencing runs.
        pool_artifact = process.all_inputs()[0]
        pool_artifact_parent_process = pool_artifact.parent_process
        pool_artifact_demux = lims.get(pool_artifact.uri + '/demux')

        run_id = pool_artifact.name  # Assume run id is set as pool name using placement/artifact/set_runid_name
        sample_artifacts = []  # sample artifacts before pooling
        sample_projects = {}

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

        for node in pool_artifact_demux.getiterator('artifact'):
            if node.find('samples'):
                if len(node.find('samples').findall('sample')) == 1:
                    # if len(node.find('samples').findall('sample')) in [1, 2]:
                    sample_artifact = Artifact(lims, uri=node.attrib['uri'])
                    sample = sample_artifact.samples[0]  # 1 sample per artifact.

                    # Skip non dx samples?
                    # Check if pool with 2 samples come from same person.

                    # Get sample sequencing run and project from samplesheet
                    sample_artifact.udf['Dx Sequencing Run ID'] = run_id
                    # Use sample.name for external (clarity_portal) samples
                    if 'Sample Type' in sample.udf and 'library' in sample.udf['Sample Type']:
                        sample_artifact.udf['Dx Sequencing Run Project'] = sample_projects[sample.name]
                    else:  # Use sample_artifact.name for Dx samples (upload via Helix)
                        sample_artifact.udf['Dx Sequencing Run Project'] = sample_projects[sample_artifact.name]
                    sample_artifact.put()
                    # Only move DX production samples to post sequencing workflow
                    if sample_artifact.samples[0].project and sample_artifact.samples[0].project.udf['Application'] == 'DX':
                        sample_artifacts.append(sample_artifact)
        # print(sample_artifacts)
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
