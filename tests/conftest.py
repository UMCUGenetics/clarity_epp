from pathlib import Path
from unittest.mock import MagicMock

import pytest
from s4.clarity.process import Process

from tests.utils import build_process_from_xml
import shutil


@pytest.fixture
def clarity_mock() -> MagicMock:
    """Mock the Clarity client instance."""
    return MagicMock()


@pytest.fixture
def custom_shared_datadir(tmp_path: Path) -> Path:
    """Return a temporary copy of the shared test data.

    The test data is stored in `tests/data/` and shared across test modules. The `shared_datadir` fixture from pytest-datadir
    looks for a `data/` directory next to the test file, so it cannot find our shared data when tests are in subdirectories
    such as `tests/actions/`.

    This fixture copies the shared data to a temporary directory so tests can access the files regardless of their location.
    """
    source = Path(__file__).parent / "data"
    destination = tmp_path / "data"
    shutil.copytree(source, destination)
    return destination


@pytest.fixture
def build_process_set_1(custom_shared_datadir, clarity_mock: MagicMock) -> Process:
    set_1_data_dir = custom_shared_datadir / "process_artifact_container_set_1"
    return build_process_from_xml(
        clarity_mock=clarity_mock,
        container_file=set_1_data_dir / "test_container.xml",
        artifact_outputs_file=set_1_data_dir / "test_process_outputs_analyte.xml",
        process_file=set_1_data_dir / "test_process_single_input_output_map.xml",
    )
