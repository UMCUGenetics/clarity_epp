import sys

from clarity_epp.export import sample


class MyMock:
    def __init__(self, udf):
        self.udf = udf


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
