"""Clarity epp package."""

from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
import smtplib
import mimetypes

from genologics.entities import Artifact


def get_sequence_name(artifact):
    """Generate sequence name."""
    sample_numbers = []
    for sample in artifact.samples:
        if 'Dx Monsternummer' in sample.udf:
            sample_numbers.append(sample.udf['Dx Monsternummer'])

    if sample_numbers:
        sequence_name = '-'.join(sample_numbers)
    else:  # non Dx sample
        sequence_name = artifact.sample[0].name

    return sequence_name


def get_sample_artifacts_from_pool(lims, pool_artifact):
    """Get sample artifacts from (sequence) pool."""
    sample_artifacts = []
    pool_artifact_demux = lims.get(pool_artifact.uri + '/demux')
    for node in pool_artifact_demux.getiterator('artifact'):
        if node.find('samples'):
            if len(node.find('samples').findall('sample')) in [1, 2]:
                sample_artifact = Artifact(lims, uri=node.attrib['uri'])

                # Check if sample_artifact with 2 samples are from the same person
                if len(sample_artifact.samples) == 2:
                    if (
                        'Dx Persoons ID' in sample_artifact.samples[0].udf or
                        'Dx Persoons ID' in sample_artifact.samples[1].udf or
                        sample_artifact.samples[0].udf['Dx Persoons ID'] == sample_artifact.samples[1].udf['Dx Persoons ID']
                    ):
                        sample_artifacts.append(sample_artifact)
                else:
                    sample_artifacts.append(sample_artifact)
    return sample_artifacts






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
