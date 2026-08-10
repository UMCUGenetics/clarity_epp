import smtplib
from email.message import EmailMessage
from utils.process import get_step_url_from_process_id
from services.clarity import ClarityService


from config import settings
from templates import render_template


def send_mail(receivers: list[str], subject: str, content: str):
    """
    Send an email.

    Args:
        receivers: Email recipients.
        subject: The subject of the email.
        content: The content of the email.
    """

    message = EmailMessage()

    message["From"] = settings.email.from_email
    message["To"] = ", ".join(receivers)
    message["Subject"] = subject

    message.set_content(content, subtype="html")
    with smtplib.SMTP(settings.email.host) as smtp:
        smtp.send_message(message)


def send_sequencing_run_qc_email(lims: ClarityService, process_id: str):
    """
    Send LIMS QC Controle email.

    Args:
        lims: Clarity LIMS service.
        process_id: Clarity process ID.
    """

    process = lims.processes.from_limsid(process_id)
    artifact = process.all_inputs()[0]
    escalation = process.step.actions.escalation

    context = {
        "sequencing_run": artifact.name,
        "technician": process.technician.name,
        "next_action": (process.step.actions.next_actions[0]["action"]),
        "conversion_ok": process.udf.get("Conversie rapport OK?"),
        "error_description": process.udf.get("Fouten registratie (uitleg)"),
        "error_cause": process.udf.get("Fouten registratie (oorzaak)"),
        "manager_review": (
            {
                "author": escalation["author"].name,
                "request": escalation["request"],
            }
            if escalation #check needed
            else None
        ),
    }

    content = render_template("sequencing_run_qc.html", context)

    send_mail(
        receivers=settings.email.to_sequencing_run_complete,
        subject=f"LIMS QC Controle - {artifact.name}",
        content=content,
    )


def send_manager_review_email(lims: ClarityService, process_id: str):
    """
    Send manager review request email.

    Args:
        lims: Clarity LIMS service.
        process_id: Clarity process ID.
    """

    process = lims.processes.from_limsid(process_id)
    step = process.step

    link = get_step_url_from_process_id(process_id)

    content = render_template("manager_review.html", {"link": link, "step_name": step.name,})

    send_mail(
        receivers=settings.email.to_manager_review,
        subject=(
            f"Manager review aangevraagd in Clarity - "
            f"{step.name}"
        ),
        content=content,
    )