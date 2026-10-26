from pathlib import Path
from unittest.mock import MagicMock

import pytest
from s4.clarity.process import Process

from tests.utils import build_process_from_xml


@pytest.fixture
def clarity_mock() -> MagicMock:
    """Mock the Clarity client instance."""
    return MagicMock()


@pytest.fixture
def build_process_set_1(shared_datadir: Path, clarity_mock: MagicMock) -> Process:
    return build_process_from_xml(
        clarity_mock=clarity_mock,
        container_filename="process_artifact_container_set_1/test_container.xml",
        artifact_outputs_filename="process_artifact_container_set_1/test_process_outputs_analyte.xml",
        process_filename="process_artifact_container_set_1/test_process_single_input_output_map.xml",
        data_dir=shared_datadir,
    )
