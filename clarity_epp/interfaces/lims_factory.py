from genologics.lims import Lims

import config
from clarity_epp.interfaces.lims_service import LimsService


class LimsFactory:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            lims = Lims(config.baseuri, config.username, config.password)
            cls._instance = LimsService(lims)
        return cls._instance