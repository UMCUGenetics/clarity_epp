from genologics.lims import Lims

import config
from clarity_epp.interfaces.lims_service import LimsService


class LimsFactory:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            lims = LimsService()
            cls._instance = lims
        return cls._instance