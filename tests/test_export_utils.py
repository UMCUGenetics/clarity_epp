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
