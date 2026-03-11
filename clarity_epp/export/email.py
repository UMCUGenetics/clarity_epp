"""Export email functions."""
from genologics.entities import Process

from .. import send_email


def sequencing_run(lims, email_settings, process_id):
    process = Process(lims, id=process_id)
    artifact = process.all_inputs()[0]

    subject = "LIMS QC Controle - {0}".format(artifact.name)

    message = "Sequencing Run: {0}\n".format(artifact.name)
    message += "Technician: {0}\n".format(process.technician.name)
    message += "LIMS Next Action: {0}\n\n".format(process.step.actions.next_actions[0]['action'])

    message += "UDF - Conversie rapport OK?: {0}\n".format(process.udf['Conversie rapport OK?'])
    if 'Fouten registratie (uitleg)' in process.udf:
        message += "UDF - Fouten registratie (uitleg): {0}\n".format(process.udf['Fouten registratie (uitleg)'])
    if 'Fouten registratie (oorzaak)' in process.udf:
        message += "UDF - Fouten registratie (oorzaak): {0}\n".format(process.udf['Fouten registratie (uitleg)'])

    if process.step.actions.escalation:
        message += "\nManager Review LIMS:\n"
        message += "{0}: {1}\n".format(
            process.step.actions.escalation['author'].name,
            process.step.actions.escalation['request']
        )

    send_email(
        email_settings['server'], email_settings['from'], email_settings['to_sequencing_run_complete'],
        subject, message
    )


def send_mail_manager_review(email_settings, link):
        manager_subject = f"Manager review aangevraagd in Clarity - Dx srWGS Bioinformatica analyses"
        manager_message  = (
            "Manager review aangevraagd voor Clarity stap: Dx srWGS Bioinformatica analyses.\n\n"
        )
        manager_message += (
            "Voordat de manager review kan worden afgerond, moet eerst in onderstaande link "
            "Dx Manager worden geselecteerd in het veld 'Request review by' en vervolgens op "
            "'Finish step' worden geklikt.\n\n"
        )
        manager_message += f"Link naar clarity stap: {link}\n"
        
        send_email(
            email_settings['server'],
            email_settings['from'],
            email_settings['to_manager_review'],
            manager_subject,
            manager_message
        )