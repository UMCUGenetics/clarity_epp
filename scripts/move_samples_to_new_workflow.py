from genologics.lims import Lims
from genologics.entities import Workflow, Queue, Stage

import config

# Setup lims connection
baseuri = 'https://usf-lims.umcutrecht.nl'
username = 'lims_user'
password = 'lims_user_password'
lims = Lims(baseuri, username, password)

old_queue = Queue(lims, id='')  # Example: Dx Sample registratie zuivering v1.0 = 1142 (same as step id)
old_stage = Stage(lims, uri='')  # Example: Dx Sample registratie zuivering v1.0 = https://usf-lims.umcutrecht.nl/api/v2/configuration/workflows/751/stages/2119
new_workflow = Workflow(lims, id='')  # Example: Dx Exoom KAPA v1.6 = 901
skip_artifacts = ['']  # Add samples that should not be moved to new workflow

artifacts = []
print('# Old queue:', len(old_queue.artifacts))

for artifact in old_queue.artifacts:
    if artifact.name not in skip_artifacts:
        print('Move:', artifact.name)
        artifacts.append(artifact)
    else:
        print('Keep:', artifact.name)

print('# Move to new workflow:', len(artifacts))

# Move things to new workflow, uncomment to enable.
# lims.route_artifacts(artifacts, stage_uri=old_stage.uri, unassign=True)  # remove from old stage
# lims.route_artifacts(artifacts, workflow_uri=new_workflow.uri)  # add to new workflow

old_queue = Queue(lims, id='')  # Example: Dx Sample registratie zuivering v1.0 = 1142 (same as step id)
print('# Old queue:', len(old_queue.artifacts))

new_queue = Queue(lims, id='')  # Example: Dx Sample registratie zuivering v1.1 = 1342 (same as step id)
print('# New queue:', len(new_queue.artifacts))
