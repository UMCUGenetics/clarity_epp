import sys

from clarity_epp.export.sample import sample_udf_dx


class SampleMock:
    def __init__(self, name, udf_dict):
        self.name = name
        self.udf = udf_dict


def test_sample_udf_with_udf(mocker, capsys):
    # Test output for sample with known Dx-udf in database
    sample = SampleMock("test_sample", {"Dx geslacht": "Vrouw"})
    samples = {sample.name: sample}
    column_name = "test_column"

    mocker.patch('clarity_epp.export.sample.get_samples', return_value=samples)

    sample_udf_dx("lims", sys.stdout, udf="Dx geslacht", column_name=column_name)
    captured = capsys.readouterr()
    assert captured.out == f"Sample\t{column_name}\n{sample.name}\tVrouw\n"


def test_sample_udf_without_udf(mocker, capsys):
    # Test output for sample with no known udf in database
    sample = SampleMock("test_sample", {"Dx geslacht": "Vrouw"})
    samples = {sample.name: sample}
    column_name = "test_column"

    mocker.patch('clarity_epp.export.sample.get_samples', return_value=samples)

    sample_udf_dx("lims", sys.stdout, udf="udf2", column_name=column_name)
    captured = capsys.readouterr()
    assert captured.out == f"Sample\t{column_name}\n{sample.name}\tunknown\n"


def test_sample_udf_without_dx_udf(mocker, capsys):
    # Test output for sample with known udf in database, but not Dx-udf
    sample = SampleMock("test_sample", {"Geslacht": "Vrouw"})
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
