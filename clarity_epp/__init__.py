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
        if not sample.name.startswith(sample.udf['Dx Familienummer']):
            sequence_name = '{familienummer}{fam_status}{sex}{monsternummer}'.format(
                familienummer=sample.udf['Dx Familienummer'],
                fam_status=fam_status,
                sex=sex,
                monsternummer=sample.udf['Dx Monsternummer']
            )
        else:
            sequence_name = sample.name
    return sequence_name


def send_email(server, sender, receivers, subject, text, attachment=None):
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

    s = smtplib.SMTP(server)
    s.sendmail(sender, receivers, mail.as_string())
    s.quit()


def convert_location(well):
    """Converts well to numbered location."""
    order = [
        'A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 
        'A3', 'B3', 'C3', 'D3', 'E3', 'F3', 'G3', 'H3', 'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4', 
        'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5', 'H5', 'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6', 
        'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7', 'A8', 'B8', 'C8', 'D8', 'E8', 'F8', 'G8', 'H8', 
        'A9', 'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9', 'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10', 'H10', 
        'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11', 'A12', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12', 'H12'
    ]
    order = dict(zip(order, range(len(order))))
    location = order[well] + 1
    return location