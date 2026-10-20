"""Step  placement functions."""

from genologics.entities import Process, ProtocolStep, Step, StepActions


def finish_protocol_complete(lims, process_id):
    """Finish next step after current step is finished (Dx Mark protocol complete)."""
    process = Process(lims, id=process_id)
    inputs = ''
    actions = []

    # Check all analytes
    for analyte in process.analytes()[0]:
        analyte_workflow_stages_and_statuses = analyte.workflow_stages_and_statuses
        if analyte_workflow_stages_and_statuses[-1][2] == 'Dx Mark protocol complete' and analyte_workflow_stages_and_statuses[-1][1] == 'QUEUED':
            actions.append({'action': 'complete', 'artifact': analyte})
            step_uri = analyte_workflow_stages_and_statuses[-1][0].step.uri
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


def get_next_LP_and_DX_dilution_steps(lims, duplicate_step):
    """Gets both available "Dx nM verdunning Myra" next step options and returns these ProtocolSteps.

    Args:
        lims (object): Lims connection
        duplicate_step (object): "Dx sample duplicate" Step object

    Returns:
        tuple[object,object]:
        Next "Dx nM verdunning Myra LP" ProtocolStep object
        Next "Dx nM verdunning Myra DX" ProtocolStep object
    """
    duplicate_protocolstep = duplicate_step.configuration
    duplicate_protocolstep_uri = lims.get(duplicate_protocolstep.uri)
    for node in duplicate_protocolstep_uri.iter('transition'):
        next_dilute_protocolstep = ProtocolStep(lims, uri=node.attrib['next-step-uri'])
        if "LP" in next_dilute_protocolstep.name:
            LP_step = next_dilute_protocolstep
        elif "DX" in next_dilute_protocolstep.name:
            DX_step = next_dilute_protocolstep
    return LP_step, DX_step


def get_and_set_next_step_based_on_artifact_extension(lims, process_id):
    """Get next "Dx nM verdunning Myra .." ProtocolSteps and set nextstep action with correct step based on artifact extension.

    Args:
        lims (object): Lims connection
        process_id (str): Process ID
    """
    duplicate_step = Step(lims, id=process_id)
    LP_step, DX_step = get_next_LP_and_DX_dilution_steps(lims, duplicate_step)
    duplicate_step_actions = duplicate_step.actions
    for action in duplicate_step_actions.next_actions:
        extension = action["artifact"].name.split('_')[-1]
        if extension == "LPsrWGS":
            action["action"] = "nextstep"
            action["step"] = LP_step
        elif extension == "srWGS":
            action["action"] = "nextstep"
            action["step"] = DX_step
    duplicate_step_actions.put()
