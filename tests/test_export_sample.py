import sys

import genologics

from clarity_epp.export.sample import removed_samples, sample_udf_dx


class ProjectMock:
    def __init__(self, name):
        self.name = name
        self.udf = {'Application': 'DX'}


class SampleMock:
    def __init__(self, name, udf={}, date_received="2024-01-01"):
        self.name = name
        self.udf = udf
        self.date_received = date_received


def test_removed_samples_skip_old_sample(mocker, capsys):
    sample = SampleMock("test_sample", date_received="2023-01-01")
    project = ProjectMock('test_project')

    mocker.patch('genologics.lims.Lims.get_projects', return_value=[project])
    mocker.patch('genologics.lims.Lims.get_samples', return_value=[sample])

    removed_samples(genologics.lims.Lims, sys.stdout)
    captured = capsys.readouterr()
    assert captured.out == (
        'Datum verwijderd\tSample\tSample project\tWerklijst\tOnderzoeks nummer\t'
        'Onderzoeks indicatie\tVerwijderd uit stap\tStatus\n'
    )


def test_sample_udf_with_udf(mocker, capsys):
    # Test output for sample with known Dx-udf in database
    sample = SampleMock("test_sample", udf={"Dx geslacht": "Vrouw"})
    samples = {sample.name: sample}
    column_name = "test_column"

    mocker.patch('clarity_epp.export.sample.get_samples', return_value=samples)

    sample_udf_dx("lims", sys.stdout, udf="Dx geslacht", column_name=column_name)
    captured = capsys.readouterr()
    assert captured.out == f"Sample\t{column_name}\n{sample.name}\tVrouw\n"


def test_sample_udf_without_udf(mocker, capsys):
    # Test output for sample with no known udf in database
    sample = SampleMock("test_sample", udf={"Dx geslacht": "Vrouw"})
    samples = {sample.name: sample}
    column_name = "test_column"

    mocker.patch('clarity_epp.export.sample.get_samples', return_value=samples)

    sample_udf_dx("lims", sys.stdout, udf="udf2", column_name=column_name)
    captured = capsys.readouterr()
    assert captured.out == f"Sample\t{column_name}\n{sample.name}\tunknown\n"


def test_sample_udf_without_dx_udf(mocker, capsys):
    # Test output for sample with known udf in database, but not Dx-udf
    sample = SampleMock("test_sample", udf={"Geslacht": "Vrouw"})
    samples = {sample.name: sample}
    column_name = "test_column"

    mocker.patch('clarity_epp.export.sample.get_samples', return_value=samples)

    sample_udf_dx("lims", sys.stdout, udf="Geslacht", column_name=column_name)
    captured = capsys.readouterr()
    assert captured.out == f"Sample\t{column_name}\nWarning, udf is not type \'Dx\'\n"


def test_sample_udf_no_samples(mocker, capsys):
    # Test output for sample not known in database
    mocker.patch('clarity_epp.export.sample.get_samples', return_value=[])

    sample_udf_dx("lims", sys.stdout)
    captured = capsys.readouterr()
    assert captured.out == "no_sample_found\n"
