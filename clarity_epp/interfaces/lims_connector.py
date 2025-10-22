from typing import Any

from genologics.entities import Process
from genologics.lims import Lims
import config


class LimsInterface:
    def __init__(self, baseuri, username, password):
        self.lims = Lims(config.baseuri, config.username, config.password)

    def get_samples_by_project_id(self, project_id: str) -> tuple[list[Any], list[dict[str, str | None]]] | list[Any]:
        """
        Get samples by project ID.

        Args:
            project_id:

        Returns:

        """
        return self.lims.get_samples(projectlimsid=project_id)

    def get_samples_by_udf(self, udf: dict) -> tuple[list[Any], list[dict[str, str | None]]] | list[Any]:
        """
        Get samples by UDF.

        Args:
            udf:

        Returns:
            object: Samples object

        """
        return self.lims.get_samples(udf=udf)

    def get_process_by_id(self, process_id: object) -> Process:
        """
        Retrieves a LIMS Process by ID.

        Args:
            process_id: The process id to look for.

        Returns:
            object: Process object

        """
        return Process(self.lims, id=process_id)

    def get_artifacts_by_sample_id(self, sample_id: object) -> list[Any] | tuple[list[Any], list[dict[str, str | None]]]:
        """
        Get artifacts by sample ID.

        Args:
            sample_id:

        Returns:

        """
        return self.lims.get_artifacts(samplelimsid=sample_id, resolve=True, type="Analyte")

    def get_file_contents_by_file_id(self, file_id):
        return self.lims.get_file_contents(file_id).data.decode('utf-8')

# Singleton instantie
_lims_interface_instance = None

def get_lims_interface():
    global _lims_interface_instance
    if _lims_interface_instance is None:
        _lims_interface_instance = LimsInterface(config.baseuri, config.username, config.password)
    return _lims_interface_instance