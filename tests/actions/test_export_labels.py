from io import StringIO
from unittest.mock import MagicMock, patch
from s4.clarity.process import Process

from clarity_epp.actions import export_labels


class TestExportLabelsContainer:
    def test_default_succeeds(self, build_process_set_1: Process, clarity_mock: MagicMock) -> None:
        process = build_process_set_1
        output_file = StringIO()

        with patch("clarity_epp.actions.export_labels.ClarityFactory.get_instance", return_value=clarity_mock):
            export_labels.export_labels_container(
                process_id=process.limsid,
                output_file=output_file,
            )

        output_file.seek(0)
        assert output_file.readline() == "Container\r\n"
        assert output_file.readline() == f"{process.outputs[0].container.name}\r\n"

    def test_with_artifact_succeeds(self, build_process_set_1: Process, clarity_mock: MagicMock) -> None:
        process = build_process_set_1
        output_file = StringIO()

        with patch("clarity_epp.actions.export_labels.ClarityFactory.get_instance", return_value=clarity_mock):
            export_labels.export_labels_container(
                process_id=process.limsid,
                with_artifacts=True,
                description=None,
                output_file=output_file,
            )

        output_file.seek(0)
        assert output_file.readline() == "Container    Sample\r\n"
        assert output_file.readline() == f"{process.outputs[0].name}    {process.outputs[0].container.name}\r\n"
