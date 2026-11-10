"""Clarity services encapsulate the business logic required to interact with Clarity LIMS and execute laboratory workflows.

This keeps business logic reusable and consistent, while separating it from CLI commands, data access and general-purpose
utilities.
"""

from typing import TYPE_CHECKING, Any

import s4.clarity
from s4.clarity.process import Process
from tenacity import RetryError, Retrying, stop_after_attempt, wait_fixed

from clarity_epp.core.config import settings

# In order to make autocomplete available in IDEs
if TYPE_CHECKING:

    class ClarityServiceType(s4.clarity.LIMS):
        """Provide the LIMS type for ClarityService to enable autocomplete in IDEs."""

else:
    ClarityServiceType = object


class ClarityService(ClarityServiceType):
    """Provide a unified interface for interacting with Clarity LIMS.

    Wraps the underlying LIMS connector to expose its functionality while allowing additional
    application-specific methods to be defined.
    """

    def __init__(self, connector: s4.clarity.LIMS):
        """Initialize the ClarityService with a LIMS connector."""
        self._lims = connector

    def __getattr__(self, name) -> Any:
        """If an attribute does not exist in ClarityService, then check whether it exists in self._lims."""
        return getattr(self._lims, name)

    def get_process(self, process_id: str) -> Process:
        """Get process by id.

        NOTE: In this particular case, the processes.from_limsid(process_id) should be used directly from the LIMS object.
        This method is added here to provide a clear and simple example of how to add methods to the ClarityService class
        while still allowing access to all methods of the underlying LIMS object.

        Args:
            process_id: Clarity process id.

        Returns:
            Process: Clarity process.
        """
        return self._lims.processes.from_limsid(process_id)


class ClarityFactory:
    """Create and provide a Clarity LIMS service instance."""

    _instance: ClarityService | None = None

    @classmethod
    def get_instance(cls) -> ClarityService:
        """Get a ClarityService instance using configuration settings.

        Returns:
            ClarityService: ClarityService instance.

        Raises:
            ConnectionError: If the connection to Clarity LIMS fails.
        """
        if cls._instance is None:
            lims = s4.clarity.LIMS(
                root_uri=f"{settings.clarity.base_url}/api/v2/",
                username=settings.clarity.username,
                password=settings.clarity.password.get_secret_value(),
                timeout=settings.clarity.timeout,
            )
            try:
                for lims_connection_attempt in Retrying(stop=stop_after_attempt(2), wait=wait_fixed(1)):
                    with lims_connection_attempt:
                        _ = lims.versions
            except RetryError as error:
                raise ConnectionError("Could not connect to Clarity LIMS.") from error
            cls._instance = ClarityService(lims)
        return cls._instance
