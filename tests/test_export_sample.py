import sys

from clarity_epp.export import sample


class MyMock:
    def __init__(self, udf):
        self.udf = udf


def test_sample_udf_withudf(mocker, capsys):
    # Test output for sample with known Dx-udf in database
    samples_mock[sample_name] = MyMock({"Dx geslacht": "Vrouw"})
    patched_clarity_epp = mocker.patch(
        'clarity_epp.export.sample.get_samples',
        return_value=samples_mock
    )
    sample.sample_udf_dx("lims", sys.stdout, udf="Dx geslacht", column_name=column_name)
    captured = capsys.readouterr()
    assert captured.out == f"Sample\t{column_name}\n{sample_name}\tVrouw\n"


def test_sample_udf_withoutudf(mocker, capsys):
    # Test output for sample with no known udf in database
    samples_mock[sample_name] = MyMock({"Dx geslacht": "Vrouw"})
    patched_clarity_epp = mocker.patch(
        'clarity_epp.export.sample.get_samples',
        return_value=samples_mock
    )
    sample.sample_udf_dx("lims", sys.stdout, udf="udf2", column_name=column_name)
    captured = capsys.readouterr()
    assert captured.out == f"Sample\t{column_name}\n{sample_name}\tunknown\n"

def test_sample_udf_withoutdxudf(mocker, capsys):
    # Test output for sample with known udf in database, but not Dx-udf
    samples_mock[sample_name] = MyMock({"Geslacht": "Vrouw"})
    patched_clarity_epp = mocker.patch(
        'clarity_epp.export.sample.get_samples',
        return_value=samples_mock
    )
    sample.sample_udf_dx("lims", sys.stdout, udf="Geslacht", column_name=column_name)
    captured = capsys.readouterr()
    assert captured.out == f"Sample\t{column_name}\nWarning, udf is not type \'Dx\'\n"


def test_sample_udf_nosamples(mocker, capsys):
    # Test output for sample not known in database
    samples_mock[sample_name] = MyMock({"Dx geslacht": "Vrouw"})
    patched_clarity_epp = mocker.patch(
        'clarity_epp.export.sample.get_samples',
        return_value=None
    )
    sample.sample_udf_dx("lims", sys.stdout)
    captured = capsys.readouterr()
    assert captured.out == "no_sample_found\n"

column_name = "test_column"
sample_name = "test_sample"
samples_mock = {}
