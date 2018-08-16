"""Clarity epp package."""

from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
import smtplib
import mimetypes


def get_sequence_name(sample):
    """Generate sequence name."""
    try:
        # Set fam_status
        if sample.udf['Dx Familie status'] == 'Kind':
            fam_status = 'C'
        elif sample.udf['Dx Familie status'] == 'Ouder':
            fam_status = 'P'

        # Set sex
        if sample.udf['Dx Geslacht'] == 'Man':
            sex = 'M'
        elif sample.udf['Dx Geslacht'] == 'Vrouw':
            sex = 'F'
        elif sample.udf['Dx Geslacht'] == 'Onbekend':
            sex = 'O'
    except KeyError:  # None DX sample, use sample.name as sequence name.
        sequence_name = sample.name
    else:
        sequence_name = '{familienummer}{fam_status}{sex}{monsternummer}'.format(
            familienummer=sample.udf['Dx Familienummer'],
            fam_status=fam_status,
            sex=sex,
            monsternummer=sample.udf['Dx Monsternummer']
        )

    return sequence_name


def send_email(sender, receivers, subject, text, attachment=None):
    """Send emails."""
    mail = MIMEMultipart()
    mail['Subject'] = subject
    mail['From'] = sender
    mail['To'] = ';'.join(receivers)

    if attachment:
        filename = attachment.split('/')[-1]
        fp = open(attachment, 'rb')
        ctype, encoding = mimetypes.guess_type(attachment)
        if ctype is None or encoding is not None:
            # No guess could be made, or the file is encoded (compressed), so
            # use a generic bag-of-bits type.
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        msg = MIMEBase(maintype, subtype)
        msg.set_payload(fp.read())
        fp.close()
        # Encode the payload using Base64
        encoders.encode_base64(msg)
        msg.add_header('Content-Disposition', 'attachment', filename=filename)
        mail.attach(msg)

    msg = MIMEText(text)
    mail.attach(msg)

    s = smtplib.SMTP('smtp-open.umcutrecht.nl')
    s.sendmail(sender, receivers, mail.as_string())
    s.quit()
