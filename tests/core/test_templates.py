import pytest

from clarity_epp.core.templates import render_template


class TestRenderTemplate:
    @pytest.mark.parametrize(
        ("include_description", "expected_rows"),
        [
            (False, ["container1"]),
            (True, ["desc1    container1"]),
        ],
        ids=["container_only", "container_with_description"],
    )
    def test_template_label_printer_container(self, include_description, expected_rows):
        """Test the render_template function with the label_printer_container_sample template.

        Args:
            include_description: Whether to include a description in the output.
            expected_rows: The expected data rows in the output.
        """
        container_artifacts = [{"artifact_name": "artifact1", "container_name": "container1", "description": "desc1"}]
        rendered_output = render_template(
            "instruments/label_printer_container.tsv",
            artifacts=container_artifacts,
            include_description=include_description,
        )
        rendered_lines = rendered_output.splitlines()
        assert rendered_lines == expected_rows

    @pytest.mark.parametrize(
        ("include_description", "expected_rows"),
        [
            (False, ["artifact1    container1"]),
            (True, ["desc1    artifact1    container1"]),
        ],
        ids=["container_with_sample", "container_with_sample_and_description"],
    )
    def test_template_label_printer_container_with_artifacts(self, include_description, expected_rows):
        """Test the render_template function with the label_printer_container_sample template.

        Args:
            include_description: Whether to include a description in the output.
            expected_rows: The expected data rows in the output.
        """
        container_artifacts = [{"artifact_name": "artifact1", "container_name": "container1", "description": "desc1"}]
        rendered_output = render_template(
            "instruments/label_printer_container_sample.tsv",
            artifacts=container_artifacts,
            include_description=include_description,
        )
        rendered_lines = rendered_output.splitlines()
        assert rendered_lines == expected_rows
