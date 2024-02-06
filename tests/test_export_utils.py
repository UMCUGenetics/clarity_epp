import sys

from unittest.mock import patch

from genologics.lims import Lims
from genologics.entities import Artifact

from clarity_epp.export import utils
from clarity_epp.export import sample


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


def test_get_samples():
    # import pytest
    # pytest.fixture(scope="function")
    # def mock_get_upload_state(mocker):
    #    return mocker.patch("rsync_to_rdisc.get_upload_state")
    # fake_lims = mocker.MagicMock()
    # artifact_name = "Test1"
    # test1 = if artifact_name, return samples for artifact
    # assert sample.sample_udf(lims, artifact_name) == "no_sample_found"
    # test2 = if sequencing_run and no sequencing_run_project, return all samples for run
    # test3 = if sequencing_run and sequencing_run_project, return all samples for project of run
    pass


column_name = "test_column"
sample_name = "test_sample"
udf_value = "Dx geslacht"
geslacht = "Vrouw"


class MyMock:
    def __init__(self, udf):
        self.udf = udf


samples_mock = {}
samples_mock[sample_name] = MyMock({udf_value: geslacht})


@patch('clarity_epp.export.sample.get_samples')
def test_get_samples_1(mock_get, capsys):
    mock_get.return_value = samples_mock
    sample.sample_udf("lims", sys.stdout, udf=udf_value, column_name=column_name)
    captured = capsys.readouterr()
    assert captured.out == f"Sample\t{column_name}\n{sample_name}\t{geslacht}\n"


@patch('clarity_epp.export.sample.get_samples')
def test_get_samples_2(mock_get, capsys):
    mock_get.return_value = samples_mock
    sample.sample_udf("lims", sys.stdout, udf="udf2", column_name=column_name)
    captured = capsys.readouterr()
    assert captured.out == f"Sample\t{column_name}\n{sample_name}\tunkown\n"


@patch('clarity_epp.export.sample.get_samples')
def test_get_samples_3(mock_get, capsys):
    mock_get.return_value = None
    sample.sample_udf("lims", sys.stdout)
    captured = capsys.readouterr()
    assert captured.out == "no_sample_found\n"
