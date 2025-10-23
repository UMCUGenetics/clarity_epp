from genologics.lims import Lims


class LimsService:
    def __init__(self, connector: Lims):
        self._lims = connector

    def __getattr__(self, name):
        """
        If an attribute does not exist in LimsService, then check whether it exists in self._lims.
        """
        return getattr(self._lims, name)