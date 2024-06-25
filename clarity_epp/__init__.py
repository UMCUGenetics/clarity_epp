"""Clarity epp package."""

from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
import re
import smtplib
import mimetypes

from genologics.entities import Artifact


def get_sequence_name(artifact):
    """Generate sequence name, for combined or single samples."""
    sample_numbers = []
    for sample in artifact.samples:
        if 'Dx Monsternummer' in sample.udf:  # Use monsternummer for Dx samples
            sample_numbers.append(sample.udf['Dx Monsternummer'])

    if sample_numbers:  # Merge monsternummer for Dx samples
        sequence_name = '-'.join(sorted(sample_numbers))
    else:  # Use sample name for non Dx samples
        sequence_name = artifact.samples[0].name

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
                        'Dx Persoons ID' in sample_artifact.samples[0].udf and
                        'Dx Persoons ID' in sample_artifact.samples[1].udf and
                        sample_artifact.samples[0].udf['Dx Persoons ID'] == sample_artifact.samples[1].udf['Dx Persoons ID']
                    ):
                        sample_artifacts.append(sample_artifact)
                else:
                    sample_artifacts.append(sample_artifact)
    return sample_artifacts


def get_mix_sample_barcode(artifact):
    """Generate mix sample shortened barcode name."""
    sample_names = {}
    for sample in artifact.samples:
        if 'Dx Monsternummer' in sample.udf:
            monster = sample.udf['Dx Monsternummer']
            if re.match(r'\d{4}D\d+', monster):
                sample_names[sample] = monster[2:4], monster[5:]
            elif monster.startswith('D'):
                sample_names[sample] = monster

    barcode_name = ''
    if sample_names:
        for sample in artifact.samples:
            barcode_name += ''.join(sample_names[sample])

    return barcode_name


def get_unique_sample_id(sample):
    if 'Dx Foetus ID' in sample.udf and sample.udf['Dx Foetus ID']:
        return sample.udf['Dx Foetus ID']
    elif 'Dx Persoons ID' in sample.udf and sample.udf['Dx Persoons ID']:
        return sample.udf['Dx Persoons ID']
    else:
        return None


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


def get_index_performance(index):
    """
    Returns the performance for given index.

    Args:
        index (str): Index name.

    Returns:
        float: Performance for given index or returns None if no performance present for index.
    """
    index_performance = {
        'Dx UDP0001 v0.1  (GAACTGAGCG-TCGTGGAGCG)':	1.19,
        'Dx UDP0002 v0.1  (AGGTCAGATA-CTACAAGATA)':	0.82,
        'Dx UDP0003 v0.1  (CGTCTCATAT-TATAGTAGCT)':	0.95,
        'Dx UDP0004 v0.1  (ATTCCATAAG-TGCCTGGTGG)':	1.07,
        'Dx UDP0005 v0.1  (GACGAGATTA-ACATTATCCT)':	0.95,
        'Dx UDP0006 v0.1  (AACATCGCGC-GTCCACTTGT)':	1.21,
        'Dx UDP0007 v0.1  (CTAGTGCTCT-TGGAACAGTA)':	1.07,
        'Dx UDP0008 v0.1  (GATCAAGGCA-CCTTGTTAAT)':	1.16,
        'Dx UDP0009 v0.1  (GACTGAGTAG-GTTGATAGTG)':	1.18,
        'Dx UDP0010 v0.1  (AGTCAGACGA-ACCAGCGACA)':	1.09,
        'Dx UDP0011 v0.1  (CCGTATGTTC-CATACACTGT)':	0.82,
        'Dx UDP0012 v0.1  (GAGTCATAGG-GTGTGGCGCT)':	0.76,
        'Dx UDP0013 v0.1  (CTTGCCATTA-ATCACGAAGG)':	0.89,
        'Dx UDP0014 v0.1  (GAAGCGGCAC-CGGCTCTACT)':	1.07,
        'Dx UDP0015 v0.1  (TCCATTGCCG-GAATGCACGA)':	0.98,
        'Dx UDP0016 v0.1  (CGGTTACGGC-AAGACTATAG)':	0.93,
        'Dx UDP0017 v0.1  (GAGAATGGTT-TCGGCAGCAA)':	1.07,
        'Dx UDP0018 v0.1  (AGAGGCAACC-CTAATGATGG)':	0.74,
        'Dx UDP0019 v0.1  (CCATCATTAG-GGTTGCCTCT)':	0.81,
        'Dx UDP0020 v0.1  (GATAGGCCGA-CGCACATGGC)':	0.92,
        'Dx UDP0021 v0.1  (ATGGTTGACT-GGCCTGTCCT)':	1.01,
        'Dx UDP0022 v0.1  (TATTGCGCTC-CTGTGTTAGG)':	1.24,
        'Dx UDP0023 v0.1  (ACGCCTTGTT-TAAGGAACGT)':	1.21,
        'Dx UDP0024 v0.1  (TTCTACATAC-CTAACTGTAA)':	1.14,
        'Dx UDP0025 v0.1  (AACCATAGAA-GGCGAGATGG)':	1.02,
        'Dx UDP0026 v0.1  (GGTTGCGAGG-AATAGAGCAA)':	1.02,
        'Dx UDP0027 v0.1  (TAAGCATCCA-TCAATCCATT)':	0.83,
        'Dx UDP0028 v0.1  (ACCACGACAT-TCGTATGCGG)':	1.42,
        'Dx UDP0029 v0.1  (GCCGCACTCT-TCCGACCTCG)':	0.85,
        'Dx UDP0030 v0.1  (CCACCAGGCA-CTTATGGAAT)':	1.04,
        'Dx UDP0031 v0.1  (GTGACACGCA-GCTTACGGAC)':	0.86,
        'Dx UDP0032 v0.1  (ACAGTGTATG-GAACATACGG)':	0.80,
        'Dx UDP0033 v0.1  (TGATTATACG-GTCGATTACA)':	0.84,
        'Dx UDP0034 v0.1  (CAGCCGCGTA-ACTAGCCGTG)':	1.09,
        'Dx UDP0035 v0.1  (GGTAACTCGC-AAGTTGGTGA)':	0.78,
        'Dx UDP0036 v0.1  (ACCGGCCGTA-TGGCAATATT)':	1.08,
        'Dx UDP0037 v0.1  (TGTAATCGAC-GATCACCGCG)':	1.03,
        'Dx UDP0038 v0.1  (GTGCAGACAG-TACCATCCGT)':	0.91,
        'Dx UDP0039 v0.1  (CAATCGGCTG-GCTGTAGGAA)':	0.84,
        'Dx UDP0040 v0.1  (TATGTAGTCA-CGCACTAATG)':	0.97,
        'Dx UDP0041 v0.1  (ACTCGGCAAT-GACAACTGAA)':	1.20,
        'Dx UDP0042 v0.1  (GTCTAATGGC-AGTGGTCAGG)':	1.03,
        'Dx UDP0043 v0.1  (CCATCTCGCC-TTCTATGGTT)':	1.09,
        'Dx UDP0044 v0.1  (CTGCGAGCCA-AATCCGGCCA)':	0.96,
        'Dx UDP0045 v0.1  (CGTTATTCTA-CCATAAGGTT)':	0.87,
        'Dx UDP0046 v0.1  (AGATCCATTA-ATCTCTACCA)':	0.70,
        'Dx UDP0047 v0.1  (GTCCTGGATA-CGGTGGCGAA)':	1.20,
        'Dx UDP0048 v0.1  (CAGTGGCACT-TAACAATAGG)':	1.09,
        'Dx UDP0049 v0.1  (AGTGTTGCAC-CTGGTACACG)':	1.00,
        'Dx UDP0050 v0.1  (GACACCATGT-TCAACGTGTA)':	0.77,
        'Dx UDP0051 v0.1  (CCTGTCTGTC-ACTGTTGTGA)':	0.89,
        'Dx UDP0052 v0.1  (TGATGTAAGA-GTGCGTCCTT)':	1.01,
        'Dx UDP0053 v0.1  (GGAATTGTAA-AGCACATCCT)':	1.00,
        'Dx UDP0054 v0.1  (GCATAAGCTT-TTCCGTCGCA)':	1.32,
        'Dx UDP0055 v0.1  (CTGAGGAATA-CTTAACCACT)':	1.05,
        'Dx UDP0056 v0.1  (AACGCACGAG-GCCTCGGATA)':	0.91,
        'Dx UDP0057 v0.1  (TCTATCCTAA-CGTCGACTGG)':	0.90,
        'Dx UDP0058 v0.1  (CTCGCTTCGG-TACTAGTCAA)':	0.73,
        'Dx UDP0059 v0.1  (CTGTTGGTCC-ATAGACCGTT)':	0.99,
        'Dx UDP0060 v0.1  (TTACCTGGAA-ACAGTTCCAG)':	1.18,
        'Dx UDP0061 v0.1  (TGGCTAATCA-AGGCATGTAG)':	0.88,
        'Dx UDP0062 v0.1  (AACACTGTTA-GCAAGTCTCA)':	0.97,
        'Dx UDP0063 v0.1  (ATTGCGCGGT-TTGGCTCCGC)':	1.27,
        'Dx UDP0064 v0.1  (TGGCGCGAAC-AACTGATACT)':	0.94,
        'Dx UDP0065 v0.1  (TAATGTGTCT-GTAAGGCATA)':	0.98,
        'Dx UDP0066 v0.1  (ATACCAACGC-AATTGCTGCG)':	1.11,
        'Dx UDP0067 v0.1  (AGGATGTGCT-TTACAATTCC)':	0.95,
        'Dx UDP0068 v0.1  (CACGGAACAA-AACCTAGCAC)':	1.10,
        'Dx UDP0069 v0.1  (TGGAGTACTT-TCTGTGTGGA)':	1.42,
        'Dx UDP0070 v0.1  (GTATTGACGT-GGAATTCCAA)':	1.22,
        'Dx UDP0071 v0.1  (CTTGTACACC-AAGCGCGCTT)':	0.95,
        'Dx UDP0072 v0.1  (ACACAGGTGG-TGAGCGTTGT)':	1.15,
        'Dx UDP0073 v0.1  (CCTGCGGAAC-ATCATAGGCT)':	1.15,
        'Dx UDP0074 v0.1  (TTCATAAGGT-TGTTAGAAGG)':	1.09,
        'Dx UDP0075 v0.1  (CTCTGCAGCG-GATGGATGTA)':	1.07,
        'Dx UDP0076 v0.1  (CTGACTCTAC-ACGGCCGTCA)':	0.86,
        'Dx UDP0077 v0.1  (TCTGGTATCC-CGTTGCTTAC)':	0.88,
        'Dx UDP0078 v0.1  (CATTAGTGCG-TGACTACATA)':	1.36,
        'Dx UDP0079 v0.1  (ACGGTCAGGA-CGGCCTCGTT)':	0.94,
        'Dx UDP0080 v0.1  (GGCAAGCCAG-CAAGCATCCG)':	0.73,
        'Dx UDP0081 v0.1  (TGTCGCTGGT-TCGTCTGACT)':	1.03,
        'Dx UDP0082 v0.1  (ACCGTTACAA-CTCATAGCGA)':	1.08,
        'Dx UDP0083 v0.1  (TATGCCTTAC-AGACACATTA)':	0.96,
        'Dx UDP0084 v0.1  (ACAAGTGGAC-GCGCGATGTT)':	1.05,
        'Dx UDP0085 v0.1  (TGGTACCTAA-CATGAGTACT)':	0.92,
        'Dx UDP0086 v0.1  (TTGGAATTCC-ACGTCAATAC)':	0.95,
        'Dx UDP0087 v0.1  (CCTCTACATG-GATACCTCCT)':	1.08,
        'Dx UDP0088 v0.1  (GGAGCGTGTA-ATCCGTAAGT)':	0.96,
        'Dx UDP0089 v0.1  (GTCCGTAAGC-CGTGTATCTT)':	1.03,
        'Dx UDP0090 v0.1  (ACTTCAAGCG-GAACCATGAA)':	0.96,
        'Dx UDP0091 v0.1  (TCAGAAGGCG-GGCCATCATA)':	0.70,
        'Dx UDP0092 v0.1  (GCGTTGGTAT-ACATACTTCC)':	1.28,
        'Dx UDP0093 v0.1  (ACATATCCAG-TATGTGCAAT)':	1.01,
        'Dx UDP0094 v0.1  (TCATAGATTG-GATTAAGGTG)':	1.09,
        'Dx UDP0095 v0.1  (GTATTCCACC-ATGTAGACAA)':	0.98,
        'Dx UDP0096 v0.1  (CCTCCGTCCA-CACATCGGTG)':	1.10
    }
    if index in index_performance:
        performance = index_performance[index]
        return performance
    else:
        return None
