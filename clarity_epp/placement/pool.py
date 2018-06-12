"""Pool  placement functions."""

from genologics.entities import Artifact, Process, Workflow


def unpooling(lims, process_id):
    process = Process(lims, id=process_id)

    pool_artifact = process.all_inputs()[0]
    pool_artifact_demux = lims.get(pool_artifact.uri + '/demux')

    sample_artifacts = []  # sample artifacts before pooling
    for node in pool_artifact_demux.iter('artifact'):
        if node.find('samples'):
            if len(node.find('samples').findall('sample')) == 1:
                sample_artifacts.append(Artifact(lims, uri=node.attrib['uri']))


    lims.route_artifacts(sample_artifacts, workflow_uri=Workflow(lims, id='604').uri)  # Dx Bioinf workflow analyses v1.1
