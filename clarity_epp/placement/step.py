"""Step  placement functions."""

from genologics.entities import Process, StepActions


def finish_protocol_complete(lims, process_id):
    """Finish next step after current step is finished (Dx Mark protocol complete)."""
    process = Process(lims, id=process_id)
    inputs = ''
    actions = []

    # Check all analytes
    for analyte in process.analytes()[0]:
        analyte_workflow_stages_and_statuses = analyte.workflow_stages_and_statuses
        if analyte_workflow_stages_and_statuses[0][2] == 'Dx Mark protocol complete' and analyte_workflow_stages_and_statuses[0][1] == 'QUEUED':
            actions.append({'action': 'complete', 'artifact': analyte})
            step_uri = analyte_workflow_stages_and_statuses[0][0].step.uri
            inputs += '<input uri="{0}" replicates="1"/>'.format(analyte.uri)

    # Generate start step XML
    xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
            <tmp:step-creation xmlns:tmp="http://genologics.com/ri/step">
                <configuration uri="{0}"/>
                <inputs>
                    {1}
                </inputs>
            </tmp:step-creation>
    '''.format(step_uri, inputs)

    # Start step
    output = lims.post(
        uri=lims.get_uri('steps'),
        data=xml
    )

    # Get started step uri
    step_action_uri = output.find('actions').get('uri')
    step_actions = StepActions(lims, uri=step_action_uri)

    # Advance to next step screen
    step = step_actions.step
    step.advance()  # Next step

    # Mark everything complete
    step_actions.set_next_actions(actions)
    step_actions.put()

    # Finish step
    step.advance()
