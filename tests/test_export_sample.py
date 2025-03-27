import sys

from clarity_epp.export import sample


class SampleMock:
    def __init__(self, udf):
        self.udf = udf


def test_sample_udf_withudf(mocker, capsys):
    # Test output for sample with known Dx-udf in database
    samples_mock[sample_name] = [SampleMock({"Dx geslacht": "Vrouw"})]
    patched_clarity_epp = mocker.patch(
        'clarity_epp.export.sample.get_artifact_samples',
        return_value=samples_mock
    )
    sample.sample_udf_dx("lims", sys.stdout, udf="Dx geslacht", column_name=column_name)
    captured = capsys.readouterr()
    assert captured.out == f"Sample\t{column_name}\n{sample_name}\tVrouw\n"


def test_sample_udf_withoutudf(mocker, capsys):
    # Test output for sample with no known udf in database
    samples_mock[sample_name] = [SampleMock({})]
    patched_clarity_epp = mocker.patch(
        'clarity_epp.export.sample.get_artifact_samples',
        return_value=samples_mock
    )
    sample.sample_udf_dx("lims", sys.stdout, udf="Dx geslacht", column_name=column_name)
    captured = capsys.readouterr()
    assert captured.out == f"Sample\t{column_name}\n{sample_name}\tunknown\n"

def test_sample_udf_with_multiple_equal_values(mocker, capsys):
    # Test output for sample with no known udf in database
    samples_mock[sample_name] = [SampleMock({"Dx geslacht": "Vrouw"}), SampleMock({"Dx geslacht": "Vrouw"})]
    patched_clarity_epp = mocker.patch(
        'clarity_epp.export.sample.get_artifact_samples',
        return_value=samples_mock
    )
    sample.sample_udf_dx("lims", sys.stdout, udf="Dx geslacht", column_name=column_name)
    captured = capsys.readouterr()
    assert captured.out == f"Sample\t{column_name}\n{sample_name}\tVrouw\n"


def test_sample_udf_with_multiple_different_values(mocker, capsys):
    # Test output for sample with no known udf in database
    samples_mock[sample_name] = [SampleMock({"Dx geslacht": "Vrouw"}), SampleMock({"Dx geslacht": "Man"})]
    patched_clarity_epp = mocker.patch(
        'clarity_epp.export.sample.get_artifact_samples',
        return_value=samples_mock
    )
    sample.sample_udf_dx("lims", sys.stdout, udf="Dx geslacht", column_name=column_name)
    captured = capsys.readouterr()
    assert captured.out == f"Sample\t{column_name}\n{sample_name}\tmultiple_values_for_udf\n"

def test_sample_udf_with_multiple_missing_value(mocker, capsys):
    # Test output for sample with no known udf in database
    samples_mock[sample_name] = [SampleMock({"Dx geslacht": "Vrouw"}), SampleMock({})]
    patched_clarity_epp = mocker.patch(
        'clarity_epp.export.sample.get_artifact_samples',
        return_value=samples_mock
    )
    sample.sample_udf_dx("lims", sys.stdout, udf="Dx geslacht", column_name=column_name)
    captured = capsys.readouterr()
    assert captured.out == f"Sample\t{column_name}\n{sample_name}\tVrouw\n"

def test_sample_udf_nosamples(mocker, capsys):
    # Test output for sample not known in database
    samples_mock[sample_name] = [SampleMock({"Dx geslacht": "Vrouw"})]
    patched_clarity_epp = mocker.patch(
        'clarity_epp.export.sample.get_artifact_samples',
        return_value=None
    )
    sample.sample_udf_dx("lims", sys.stdout)
    captured = capsys.readouterr()
    assert captured.out == "no_sample_found\n"

column_name = "test_column"
sample_name = "test_sample"
samples_mock = {}
