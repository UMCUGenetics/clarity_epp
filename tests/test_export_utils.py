from genologics.lims import Lims
from genologics.entities import Artifact

from clarity_epp.export import utils


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
