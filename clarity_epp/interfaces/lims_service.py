from genologics.lims import Lims

import config


class LimsService(Lims):
    def __init__(self):
        super().__init__(config.baseuri, config.username, config.password)