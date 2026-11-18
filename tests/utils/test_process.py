import pytest
from s4.clarity.artifact import Artifact
from s4.clarity.process import Process

from clarity_epp.utils.process import get_artifact_containers_from_process


class TestGetArtifactContainersFromProcess:
    """Tests for grouping process output artifacts by container and placement."""

    @pytest.mark.parametrize(
        ("format_placement_to_position", "expected_placement"),
        [
            (True, ["A1", "B1"]),
            (False, ["A:1", "B:1"]),
        ],
        ids=["test_position_format", "test_original_placement_format"],
    )
    def test_format_placement_succeeds(
        self,
        format_placement_to_position: bool,
        expected_placement: list[str],
        process_data_well_plate: Process,
        artifacts_by_limsid_well_plate: dict[str, Artifact],
    ) -> None:
        """Verify plate placements use the requested format."""
        artifact_containers = get_artifact_containers_from_process(
            process_data_well_plate, format_placement_to_position=format_placement_to_position
        )
        assert artifact_containers == {
            "27-1438": {
                expected_placement[0]: artifacts_by_limsid_well_plate["PLATE_SAMPLE_A"],
                expected_placement[1]: artifacts_by_limsid_well_plate["PLATE_SAMPLE_B"],
            }
        }

    def test_single_artifact_single_container_succeeds(
        self,
        process_data_tube: Process,
        artifact_by_limsid_tube: Artifact,
    ) -> None:
        artifact_containers = get_artifact_containers_from_process(process_data_tube)

        assert artifact_containers == {"27-1": {"1:1": artifact_by_limsid_tube}}

    def test_multiple_artifacts_single_container_succeeds(
        self,
        process_data_well_plate: Process,
        artifacts_by_limsid_well_plate: dict[str, Artifact],
    ) -> None:
        artifact_containers = get_artifact_containers_from_process(process_data_well_plate)

        assert artifact_containers == {
            "27-1438": {
                "A:1": artifacts_by_limsid_well_plate["PLATE_SAMPLE_A"],
                "B:1": artifacts_by_limsid_well_plate["PLATE_SAMPLE_B"],
            }
        }

    def test_multiple_artifacts_multiple_container_succeeds(
        self,
        process_data_tubes: Process,
        artifacts_by_limsid_tubes: dict[str, Artifact],
    ) -> None:
        artifact_containers = get_artifact_containers_from_process(process_data_tubes)

        assert artifact_containers == {
            "27-1": {"1:1": artifacts_by_limsid_tubes["TUBE_SAMPLE_1"]},
            "27-2": {"1:1": artifacts_by_limsid_tubes["TUBE_SAMPLE_2"]},
        }
