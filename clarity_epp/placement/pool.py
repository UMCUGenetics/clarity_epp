"""Pool  placement functions."""

from genologics.entities import Artifact, Process, Workflow

import config


def unpooling(lims, process_id):
    """Unpool samples after sequencing."""
    process = Process(lims, id=process_id)

    pool_artifact = process.all_inputs()[0]
    pool_artifact_demux = lims.get(pool_artifact.uri + '/demux')
    run_id = pool_artifact.name  # Assume run id is set as pool name using placement/artifact/set_runid_name
    sample_artifacts = []  # sample artifacts before pooling
    for node in pool_artifact_demux.iter('artifact'):
        if node.find('samples'):
            if len(node.find('samples').findall('sample')) == 1:
                sample_artifact = Artifact(lims, uri=node.attrib['uri'])
                sample_artifact.udf['Dx Sequencing Run ID'] = run_id
                sample_artifact.put()
                sample_artifacts.append(sample_artifact)

    lims.route_artifacts(sample_artifacts, workflow_uri=Workflow(lims, id=config.post_seq_workflow).uri)  # Dx Post sequencing v1.0
