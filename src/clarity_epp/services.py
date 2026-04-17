from typing import TYPE_CHECKING, Any

# import genologics.lims
# from genologics.entities import Artifact, Process
import s4.clarity
from tenacity import RetryError, Retrying, stop_after_attempt, wait_fixed

from clarity_epp.config import settings

# In order to make autocomplete available in IDEs
if TYPE_CHECKING:
    class ClarityServiceType(s4.clarity.LIMS): ...
else:
    ClarityServiceType = object

class ClarityService(ClarityServiceType):
    def __init__(self, connector: s4.clarity.LIMS):
        self._lims = connector

    def __getattr__(self, name) -> Any:
        """
        If an attribute does not exist in ClarityService, then check whether it exists in self._lims.
        """
        return getattr(self._lims, name)

class ClarityFactory:
    _instance: s4.clarity.LIMS = None

    @classmethod
    def get_instance(cls) -> ClarityService:
        if cls._instance is None:
            lims = s4.clarity.LIMS(
                root_uri=f"{settings.clarity.base_url}/api/v2/",
                username=settings.clarity.username,
                password= settings.clarity.password.get_secret_value(),
                timeout=settings.clarity.timeout
            )
            try:
                for lims_connection_attempt in Retrying(stop=stop_after_attempt(2), wait=wait_fixed(1)):
                    with lims_connection_attempt:
                        _ = lims.versions
            except RetryError:
                raise Exception("Could not connect to Clarity LIMS.")
            cls._instance = lims
        return cls._instance
