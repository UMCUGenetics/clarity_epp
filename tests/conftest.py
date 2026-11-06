import shutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from s4.clarity.artifact import Artifact
from s4.clarity.process import Process

from tests.utils import build_process_from_xml


@pytest.fixture
def clarity_mock() -> MagicMock:
    """Mock the Clarity client instance."""
    return MagicMock()


@pytest.fixture(scope="session")
def custom_shared_datadir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Return a temporary copy of the shared test data.

    The test data is stored in `tests/data/` and shared across test modules. The `shared_datadir` fixture from pytest-datadir
    looks for a `data/` directory next to the test file, so it cannot find our shared data when tests are in subdirectories
    such as `tests/actions/`.

    This fixture copies the shared data to a temporary directory so tests can access the files regardless of their location.
    """
    source = Path(__file__).parent / "data"
    destination = tmp_path_factory.mktemp("shared-data") / "data"
    shutil.copytree(source, destination)
    return destination


@pytest.fixture
def process_data_well_plate(custom_shared_datadir: Path, clarity_mock: MagicMock) -> Process:
    """Process testdata reflecting an incomplete process, with two artifacts (samples) located on the same container.

    Args:
        custom_shared_datadir: Shared test data directory.
        clarity_mock: Mocked Clarity client instance.

    Returns:
        Clarity process object with two artifacts on the same container (reflecting a well plate).
    """
    return build_process_from_xml(
        clarity_mock=clarity_mock,
        artifact_outputs_files=[
            custom_shared_datadir / "artifact" / "analyte_well_plate_1.xml",
            custom_shared_datadir / "artifact" / "analyte_well_plate_2.xml",
        ],
        container_files=[custom_shared_datadir / "container" / "container_well_plate.xml"],
        process_file=custom_shared_datadir / "process" / "process_well_plate_multiple_output_map.xml",
    )


@pytest.fixture
def process_data_tube(custom_shared_datadir: Path, clarity_mock: MagicMock) -> Process:
    """Process testdata reflecting a single artifact located in single container (tube).

    Args:
        custom_shared_datadir: Shared test data directory.
        clarity_mock: Mocked Clarity client instance.

    Returns:
        Clarity process object with one artifact in one tube.
    """
    return build_process_from_xml(
        clarity_mock=clarity_mock,
        artifact_outputs_files=[custom_shared_datadir / "artifact" / "analyte_tube_1.xml"],
        container_files=[custom_shared_datadir / "container" / "container_tube_1.xml"],
        process_file=custom_shared_datadir / "process" / "process_tube_single_output_map.xml",
    )


@pytest.fixture
def process_data_tubes(custom_shared_datadir: Path, clarity_mock: MagicMock) -> Process:
    """Process testdata reflecting a process, with two artifacts (samples) located on different containers.

    The containers reflect two tubes, which could have the same placement (e.g., "A:1") and are differentiated by their
    container IDs.

    Args:
        custom_shared_datadir: Shared test data directory.
        clarity_mock: Mocked Clarity client instance.

    Returns:
        Clarity process object with two artifacts on different containers (reflecting two tubes).
    """
    return build_process_from_xml(
        clarity_mock=clarity_mock,
        artifact_outputs_files=[
            custom_shared_datadir / "artifact" / "analyte_tube_1.xml",
            custom_shared_datadir / "artifact" / "analyte_tube_2.xml",
        ],
        container_files=[
            custom_shared_datadir / "container" / "container_tube_1.xml",
            custom_shared_datadir / "container" / "container_tube_2.xml",
        ],
        process_file=custom_shared_datadir / "process" / "process_tubes_multiple_output_map.xml",
    )


@pytest.fixture
def artifacts_by_limsid_well_plate(process_data_well_plate: Process) -> dict[str, Artifact]:
    """Get Index well-plate output artifacts by LIMS ID.

    Args:
        process_data_well_plate: Process containing the well-plate outputs.

    Returns:
        Well-plate output artifacts indexed by LIMS ID.
    """
    return {artifact.limsid: artifact for artifact in process_data_well_plate.outputs}


@pytest.fixture
def artifact_by_limsid_tube(process_data_tube: Process) -> Artifact:
    """Return the single tube output artifact.

    Args:
        process_data_tube: Process containing one tube output.

    Returns:
        The tube output artifact.
    """
    return process_data_tube.outputs[0]


@pytest.fixture
def artifacts_by_limsid_tubes(process_data_tubes: Process) -> dict[str, Artifact]:
    """Index tube output artifacts by LIMS ID.

    Args:
        process_data_tubes: Process containing the tube outputs.

    Returns:
        Tube output artifacts indexed by LIMS ID.
    """
    return {artifact.limsid: artifact for artifact in process_data_tubes.outputs}
