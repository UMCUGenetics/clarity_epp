# from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock
from xml.etree import ElementTree

from s4.clarity.artifact import Artifact
from s4.clarity.container import Container
from s4.clarity.process import Process


def get_xml_root_from_data_file(data_file: Path) -> ElementTree.Element:
    """Parse an XML file and return its root element.

    Args:
        data_file: Path to the XML file.

    Returns:
        Root element of the parsed XML document.
    """
    return ElementTree.parse(data_file).getroot()


def get_artifact_from_link(node: ElementTree.Element, artifacts_by_limsid: dict[str, Artifact]) -> Artifact | MagicMock:
    """Resolve an artifact link using an artifact lookup.

    Args:
        node: XML node containing an artifact LIMS ID.
        artifacts_by_limsid: Artifacts indexed by LIMS ID.

    Returns:
        The matching artifact or a mock when no artifact is found.
    """
    artifact = artifacts_by_limsid.get(node.get("limsid"))
    return artifact if artifact is not None else MagicMock()


def build_process_from_xml(
    clarity_mock: MagicMock,
    artifact_outputs_files: list[Path],
    container_files: list[Path],
    process_file: Path,
) -> Process:
    """Build a process and its linked artifacts and containers from XML files.

    Args:
        clarity_mock: Mock Clarity client used to construct the LIMS objects.
        artifact_outputs_files: XML files defining process output artifacts.
        container_files: XML files defining linked containers.
        process_file: XML file defining the process and output mappings.

    Returns:
        Process constructed from the provided XML data.
    """
    output_artifacts = [
        Artifact(lims=clarity_mock, xml_root=get_xml_root_from_data_file(file)) for file in artifact_outputs_files
    ]
    artifacts_by_limsid = {artifact.limsid: artifact for artifact in output_artifacts}

    clarity_mock.artifacts.from_link_node.side_effect = lambda node: get_artifact_from_link(node, artifacts_by_limsid)

    containers = [Container(lims=clarity_mock, xml_root=get_xml_root_from_data_file(file)) for file in container_files]
    containers_by_limsid = {container.limsid: container for container in containers}
    clarity_mock.containers.from_link_node.side_effect = lambda node: containers_by_limsid[node.get("limsid")]

    process = Process(
        lims=clarity_mock,
        xml_root=get_xml_root_from_data_file(process_file),
    )
    clarity_mock.processes.from_limsid.return_value = process
    return process
