from typing import Any, TYPE_CHECKING

import genologics.lims
from genologics.entities import Artifact, Process
from tenacity import Retrying, RetryError, stop_after_attempt, wait_fixed


from clarity_epp.config import settings

# In order to make autocomplete available in IDEs
if TYPE_CHECKING:
    class ClarityServiceType(genologics.lims.Lims): ...
else:
    ClarityServiceType = object

class ClarityService(genologics.lims.Lims):
class ClarityService(ClarityServiceType):
    def __init__(self, connector: genologics.lims.Lims):
        self._lims = connector

    def __getattr__(self, name) -> Any:
        """
        If an attribute does not exist in ClarityService, then check whether it exists in self._lims.
        """
        return getattr(self._lims, name)

    def get_process(self, process_id: str) -> Process:
        """Get process by id.

        Args:
            process_id (str): Clarity process id.

        Returns:
            Process: Clarity process object.

        """
        process = Process(self, id=process_id)
        return process

    def get_process_well_plate(self, process: Process) -> dict[str, Artifact]:
        """Get well plate artifacts for a given process id.

        Args:
            process (Process): Clarity process object.

        Returns:
            dict[str, Artifact]: Dictionary with well positions as keys and Artifacts as values.

        """
        well_plate = {}
        for placement, artifact in process.output_containers()[0].placements.items():
            placement = "".join(placement.split(":"))
            well_plate[placement] = artifact

        return well_plate

    def get_process_types_by_partial_name(self, process_types_names: list[str]) -> list[str]:
        """Get process types by partial name.

        Args:
            process_types_names (list[str]): List of partial process type names.

        Returns:
            list[str]: List of matching process type names.

        If complete name is known use lims.get_process_types(displayname="complete name")
        """
        all_process_types = self.get_process_types()
        process_types = []

        for process_type in all_process_types:
            for process_types_name in process_types_names:
                if process_types_name in process_type.name:
                    process_types.append(process_type.name)

        return process_types


class ClarityFactory:
    _instance: genologics.lims.Lims = None

    @classmethod
    def get_instance(cls) -> ClarityService:
        if cls._instance is None:
            lims = genologics.lims.Lims(
                settings.clarity.baseuri, settings.clarity.username, settings.clarity.password.get_secret_value()
            )
            genologics.lims.timeout = settings.clarity.api_timeout
            try:
                for lims_connection_attempt in Retrying(stop=stop_after_attempt(2), wait=wait_fixed(1)):
                    with lims_connection_attempt:
                        lims.check_version()
            except RetryError:
                raise Exception("Could not connect to Clarity LIMS.")
            cls._instance = ClarityService(lims)
            cls._instance = lims
        return cls._instance
