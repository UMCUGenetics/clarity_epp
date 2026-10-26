# from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree
from unittest.mock import MagicMock

from s4.clarity.artifact import Artifact
from s4.clarity.container import Container
from s4.clarity.process import Process


def get_xml_root_from_data_file(data_file: Path) -> ElementTree.Element:
    return ElementTree.parse(data_file).getroot()


def build_process_from_xml(
    clarity_mock: MagicMock,
    artifact_outputs_file,
    container_file,
    process_file,
) -> Process:
    output_artifact = Artifact(
        lims=clarity_mock,
        xml_root=get_xml_root_from_data_file(artifact_outputs_file),
    )
    clarity_mock.artifacts.from_link_node.return_value = output_artifact

    container = Container(
        lims=clarity_mock,
        xml_root=get_xml_root_from_data_file(container_file),
    )
    clarity_mock.containers.from_link_node.return_value = container

    process = Process(
        lims=clarity_mock,
        xml_root=get_xml_root_from_data_file(process_file),
    )
    clarity_mock.processes.from_limsid.return_value = process
    return process
