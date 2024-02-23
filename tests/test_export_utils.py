import sys

from genologics.lims import Lims
from genologics.entities import Artifact

from clarity_epp.export import utils
from clarity_epp.export import sample


class MyMock:
    def __init__(self, udf):
        self.udf = udf


def test_sort_96_well_plate():
    assert utils.sort_96_well_plate(['B2', 'A1', 'E1']) == ['A1', 'E1', 'B2']


def test_reverse_complement():
    assert utils.reverse_complement('CGTA') == 'TACG'


def test_sort_artifact_list():
    lims = Lims('url', username='test', password='password')
    artifact = Artifact(lims, id='12-456')
    assert utils.sort_artifact_list(artifact) == 456


def test_get_well_index():
    assert utils.get_well_index('A1') == 0
    assert utils.get_well_index('A1', one_based=True) == 1


def test_get_sample_sequence_index():
    # Dual Index
    assert utils.get_sample_sequence_index('Dx 12D NEXTflex UDI 48 (TTAGAGTC-TGTGACGA)') == ['TTAGAGTC', 'TGTGACGA']
    assert utils.get_sample_sequence_index('Dx 10G NEXTflex custom UDI 79 (TGAGGCGC-GGAGACCA)') == ['TGAGGCGC', 'GGAGACCA']
    assert utils.get_sample_sequence_index('Dx 01G Agilent SureSelect XT HS2 UDI_v2 007 (GCAGGTTC-AGAAGCAA)') == ['GCAGGTTC', 'AGAAGCAA']
    assert utils.get_sample_sequence_index('Dx 02B Agilent SureSelect XT HS2 UDI_v1 010 (TAGAGCTC-CTACCGAA)') == ['TAGAGCTC', 'CTACCGAA']

    # Single Index
    assert utils.get_sample_sequence_index('Dx 12D NEXTflex UDI 48 (TTAGAGTC)') == ['TTAGAGTC']
    assert utils.get_sample_sequence_index('Dx 10G NEXTflex custom UDI 79 (TGAGGCGC)') == ['TGAGGCGC']
    assert utils.get_sample_sequence_index('Dx 01G Agilent SureSelect XT HS2 UDI_v2 007 (GCAGGTTC)') == ['GCAGGTTC']
    assert utils.get_sample_sequence_index('Dx 02B Agilent SureSelect XT HS2 UDI_v1 010 (TAGAGCTC)') == ['TAGAGCTC']


def test_sample_udf_withudf(mocker, capsys):
    # Test output for sample with known udf in database
    patched_clarity_epp = mocker.patch(
        'clarity_epp.export.sample.get_samples',
        return_value=samples_mock
    )
    sample.sample_udf("lims", sys.stdout, udf=udf_value, column_name=column_name)
    captured = capsys.readouterr()
    assert captured.out == f"Sample\t{column_name}\n{sample_name}\t{geslacht}\n"


def test_sample_udf_withoutudf(mocker, capsys):
    # Test output for sample with no known udf in database
    patched_clarity_epp = mocker.patch(
        'clarity_epp.export.sample.get_samples',
        return_value=samples_mock
    )
    sample.sample_udf("lims", sys.stdout, udf="udf2", column_name=column_name)
    captured = capsys.readouterr()
    assert captured.out == f"Sample\t{column_name}\n{sample_name}\tunknown\n"


def test_sample_udf_nosamples(mocker, capsys):
    # Test output for sample not known in database
    patched_clarity_epp = mocker.patch(
        'clarity_epp.export.sample.get_samples',
        return_value=None
    )
    sample.sample_udf("lims", sys.stdout)
    captured = capsys.readouterr()
    assert captured.out == "no_sample_found\n"


column_name = "test_column"
sample_name = "test_sample"
udf_value = "Dx geslacht"
geslacht = "Vrouw"
samples_mock = {}
samples_mock[sample_name] = MyMock({udf_value: geslacht})
