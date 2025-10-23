from genologics.lims import Lims


class LimsService():
    def __init__(self, lims: Lims):
        self._lims = lims

    def get_samples(self, **kwargs):
        return self._lims.get_samples(**kwargs)

    def get_workflows(self, **kwargs):
        return self._lims.get_workflows(**kwargs)