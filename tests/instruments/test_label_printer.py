from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from s4.clarity.artifact import Artifact
from pytest_unordered import unordered

from clarity_epp.instruments import label_printer


def make_artifact_mock(name: str, container_name: str) -> MagicMock:
    artifact = MagicMock(spec=Artifact)
    artifact.name = name
    artifact.container = MagicMock()
    artifact.container.name = container_name
    return artifact


class TestGetArtifactContainerLabels:
    def test_single_artifact_single_container_succeeds(self) -> None:
        artifact_name = "Tube Sample 1"
        artifact_container_name = "Tube 27-1"
        artifact_sample_tube_1 = make_artifact_mock(artifact_name, artifact_container_name)

        labels = label_printer.get_artifact_container_labels({"27-1": {"1:1": artifact_sample_tube_1}})
        assert len(labels) == 1
        assert labels[0]["artifact_name"] == artifact_name
        assert labels[0]["container_name"] == artifact_container_name
        assert labels[0]["description"] is None

    def test_multiple_artifacts_single_container_succeeds(self) -> None:
        artifact_name_1 = "Well Plate Sample 1"
        artifact_container_name = "Well Plate 27-1"
        artifact_sample_well_1 = make_artifact_mock(artifact_name_1, artifact_container_name)
        artifact_name_2 = "Well Plate Sample 2"
        artifact_sample_well_2 = make_artifact_mock(artifact_name_2, artifact_container_name)

        labels = label_printer.get_artifact_container_labels(
            {
                "27-1": {
                    "A:1": artifact_sample_well_1,
                    "B:1": artifact_sample_well_2,
                }
            },
        )

        assert labels == unordered(
            [
                {"artifact_name": artifact_name_1, "container_name": artifact_container_name, "description": None},
                {"artifact_name": artifact_name_2, "container_name": artifact_container_name, "description": None},
            ]
        )

    def test_multiple_artifacts_multiple_container_succeeds(self) -> None:
        artifact_name_1 = "Tube Sample 1"
        artifact_container_1 = "Tube 27-1"
        artifact_sample_tube_1 = make_artifact_mock(artifact_name_1, artifact_container_1)
        artifact_name_2 = "Tube Sample 2"
        artifact_container_2 = "Tube 27-2"
        artifact_sample_tube_2 = make_artifact_mock(artifact_name_2, artifact_container_2)

        labels = label_printer.get_artifact_container_labels(
            {
                "27-1": {"1:1": artifact_sample_tube_1},
                "27-2": {"1:1": artifact_sample_tube_2},
            },
        )

        assert labels == unordered(
            [
                {"artifact_name": artifact_name_1, "container_name": artifact_container_1, "description": None},
                {"artifact_name": artifact_name_2, "container_name": artifact_container_2, "description": None},
            ]
        )

    def test_description_as_string_succeeds(self) -> None:
        artifact_containers = {"27-1": {"1:1": make_artifact_mock("Tube Sample 1", "Tube 27-1")}}
        description = "description_lorem_ipsum"

        labels = label_printer.get_artifact_container_labels(artifact_containers, description=description)

        assert len(labels) == 1
        assert labels[0]["description"] == description

    def test_multi_value_description_succeeds(self) -> None:
        description_1 = "description_lorem_ipsum_1"
        description_2 = "description_lorem_ipsum_2"

        labels = label_printer.get_artifact_container_labels(
            artifact_containers={
                "27-1": {"1:1": make_artifact_mock("Tube Sample 1", "Tube 27-1")},
                "27-2": {"1:1": make_artifact_mock("Tube Sample 2", "Tube 27-2")},
            },
            description=",".join([description_1, description_2]),
        )

        assert [label["description"] for label in labels] == unordered([description_1, description_2])


@pytest.mark.parametrize(
    ("with_artifacts", "expected_template"),
    [
        (False, "instruments/label_printer_container.tsv"),
        (True, "instruments/label_printer_container_sample.tsv"),
    ],
    ids=["without_artifacts", "with_artifacts"],
)
def test_export_labels_container_selects_correct_template(
    clarity_mock: MagicMock,
    with_artifacts: bool,
    expected_template: str,
) -> None:
    with (
        patch("clarity_epp.instruments.label_printer.ClarityFactory.get_instance", return_value=clarity_mock),
        patch("clarity_epp.instruments.label_printer.render_template", return_value="") as render_template,
    ):
        label_printer.export_labels_container(
            process_id="process_id_lorem_ipsum",
            with_artifacts=with_artifacts,
            output_file=StringIO(),
        )

    render_template.assert_called_once()
    assert render_template.call_args.args[0] == expected_template
