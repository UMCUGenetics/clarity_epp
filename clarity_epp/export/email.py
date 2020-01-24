"""Export email functions."""
from genologics.entities import Process

from .. import send_email


def sequencing_run(lims, email_settings, process_id):
    process = Process(lims, id=process_id)
    artifact = process.all_inputs()[0]

    subject = "LIMS - {0}".format(artifact.name)

    message = "Sequencing Run: {0}\n".format(artifact.name)
    message += "Date: {0}\n".format(process.date_run)
    message += "Technician: {0}\n\n".format(process.technician.name)

    message += "Status: {0}\n".format(process.step.actions.get_next_actions()[0]['action'])
    message += "UDF - Conversie rapport OK?: {0}\n".format(process.udf['Conversie rapport OK?'])
    if 'Fouten registratie (uitleg)' in process.udf:
        message += "UDF - Fouten registratie (uitleg): {0}\n".format(process.udf['Fouten registratie (uitleg)'])
    if 'Fouten registratie (oorzaak)' in process.udf:
        message += "UDF - Fouten registratie (oorzaak): {0}\n".format(process.udf['Fouten registratie (uitleg)'])

    if process.step.actions.escalation:
        message += "\nManager Review LIMS:\n"
        message += "{0}: {1}\n".format(process.step.actions.escalation['author'].name, process.step.actions.escalation['request'])
        message += "{0}: {1}\n".format(process.step.actions.escalation['reviewer'].name, process.step.actions.escalation['answer'])

    send_email(email_settings['from'], email_settings['to_sequencing_run_complete'], subject, message)
