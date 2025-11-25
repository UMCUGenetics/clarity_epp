import pytest

from genologics.lims import Lims
from genologics.entities import Artifact
from jinja2 import Environment, FileSystemLoader

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


@pytest.fixture
def make_info_dir1():
    info_dir = {}
    for i in range(1, 6, 1):
        info_dir[i] = {
            "name": f"sample_{i}",
            "input": "input_container",
            "well_input": f"A{i}",
            "output": "output_container",
            "well_output": f"B{i}",
        }
    return info_dir


@pytest.mark.parametrize("template, expected", [("samplesheet_template.csv", "samplesheet_result.csv")])
def test_create_samplesheet(template, make_info_dir1, expected, datadir):
    environment = Environment(loader=FileSystemLoader(datadir))
    expected = (datadir / expected).read_text()
    content = {"samples": make_info_dir1}
    result = utils.create_samplesheet(template, content, environment)
    assert result == expected


@pytest.mark.parametrize("label, expected", [
    ("Dx 01A 1057 (GAACCTGATG-AGCATATTAG)", "A1"),
    ("Dx 12H 96 (TGGTCGGCGC-GCGCCTGGAA)", "H12")
])
def test_extract_well_from_reagent_label(label, expected):
    assert utils.extract_well_from_reagent_label(label) == expected


@pytest.mark.parametrize("input_dict, expected_dict", [
    ({"key1": {"well": "D4"}, "key2": {"well": "B2"}, "key3": {"well": "C7"}},
     {"key2": {"well": "B2"}, "key3": {"well": "C7"}, "key1": {"well": "D4"}})
])
def test_sort_dict_by_nested_well_location(input_dict, expected_dict):
    assert utils.sort_dict_by_nested_well_location(input_dict, "well") == expected_dict
