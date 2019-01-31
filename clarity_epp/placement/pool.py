"""Pool  placement functions."""

from genologics.entities import Artifact, Process, Workflow

import config


def unpooling(lims, process_id):
    """Unpool samples after sequencing."""
    process = Process(lims, id=process_id)

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
            for line in sample_sheet.split('\n'):
                data = line.rstrip().split(',')
                if len(data) == 7:
                    sample_projects[data[0]] = data[5]

    for node in pool_artifact_demux.getiterator('artifact'):
        if node.find('samples'):
            if len(node.find('samples').findall('sample')) == 1:
                sample_artifact = Artifact(lims, uri=node.attrib['uri'])
                sample_artifact.udf['Dx Sequencing Run ID'] = run_id
                sample_artifact.udf['Dx Sequencing Run Project'] = sample_projects[sample_artifact.name]
                sample_artifact.put()
                if sample_artifact.samples[0].project.udf['Application'] == 'DX':  # Only move DX samples to post sequencing workflow
                    sample_artifacts.append(sample_artifact)
    lims.route_artifacts(sample_artifacts, workflow_uri=Workflow(lims, id=config.post_seq_workflow).uri)
